#!/usr/bin/env python3
"""Read-only, local browser for the Kent repertory. Python 3.10+, stdlib only.

Run: python viewer.py [--database repertory.sqlite] [--port 8765] [--no-browser]
The original source PDF stays in place; it is streamed only over loopback.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import re
import sqlite3
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

DEFAULT_DB = Path(__file__).resolve().with_name("repertory.sqlite")


class Repertory:
    def __init__(self, database=DEFAULT_DB, source=None):
        self.database = Path(database).resolve()
        self.source_override = Path(source).resolve() if source else None

    @contextlib.contextmanager
    def connect(self):
        if not self.database.is_file():
            raise FileNotFoundError(f"Database is not available: {self.database}")
        db = sqlite3.connect(self.database.as_uri() + "?mode=ro", uri=True, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        try:
            yield db
        finally:
            db.close()

    @staticmethod
    def rows(db, sql, parameters=()):
        return [dict(row) for row in db.execute(sql, parameters)]

    @staticmethod
    def has_table(db, name):
        return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None

    @staticmethod
    def decode_json(value, default=None):
        if value is None:
            return default
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value

    def metadata(self):
        with self.connect() as db:
            return {r["key"]: self.decode_json(r["value"]) for r in db.execute("SELECT key,value FROM metadata")}

    def source_path(self):
        if self.source_override:
            return self.source_override
        value = self.metadata().get("source_path")
        if not isinstance(value, str) or not value:
            return None
        path = Path(value)
        if not path.is_absolute():
            path = self.database.parent / path
        return path.resolve()

    def stats(self):
        with self.connect() as db:
            result = {}
            for table in ("sections", "pages", "rubrics", "remedies", "rubric_remedies", "cross_references", "issues"):
                result[table] = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            result["reviewed_grades"] = db.execute("SELECT COUNT(*) FROM rubric_remedies WHERE grade IS NOT NULL").fetchone()[0]
            result["candidate_grades"] = db.execute("SELECT COUNT(*) FROM rubric_remedies WHERE grade_candidate IS NOT NULL").fetchone()[0]
            result["metadata"] = {r["key"]: self.decode_json(r["value"]) for r in db.execute("SELECT key,value FROM metadata")}
        source = self.source_path()
        result["source_available"] = bool(source and source.is_file())
        return result

    def sections(self):
        with self.connect() as db:
            return self.rows(db, """SELECT s.*, (SELECT COUNT(*) FROM rubrics r WHERE r.section_id=s.id) AS rubric_count
                                  FROM sections s ORDER BY s.pdf_start,s.id""")

    def children(self, section=None, parent=None, limit=1000, offset=0):
        if parent is None and section is None:
            raise ValueError("Supply a section or parent rubric ID.")
        limit = max(1, min(int(limit), 5000))
        offset = max(0, int(offset))
        condition = "r.parent_id=?" if parent is not None else "r.section_id=? AND r.parent_id IS NULL"
        parameter = int(parent if parent is not None else section)
        with self.connect() as db:
            total = db.execute(f"SELECT COUNT(*) FROM rubrics r WHERE {condition}", (parameter,)).fetchone()[0]
            rows = self.rows(db, f"""SELECT r.*,
                  EXISTS(SELECT 1 FROM rubrics c WHERE c.parent_id=r.id) AS has_children,
                  (SELECT COUNT(*) FROM rubric_remedies m WHERE m.rubric_id=r.id) AS remedy_count
                  FROM rubrics r WHERE {condition} ORDER BY r.order_index,r.id LIMIT ? OFFSET ?""", (parameter, limit, offset))
        return {"items": rows, "total": total, "limit": limit, "offset": offset}

    def node(self, identifier):
        with self.connect() as db:
            row = db.execute("SELECT * FROM rubrics WHERE id=?", (int(identifier),)).fetchone()
            if row is None:
                raise LookupError("Rubric not found.")
            result = dict(row)
            result["section"] = dict(db.execute("SELECT * FROM sections WHERE id=?", (row["section_id"],)).fetchone())
            result["remedies"] = self.rows(db, """SELECT rr.*,r.abbreviation,r.full_name FROM rubric_remedies rr
                             LEFT JOIN remedies r ON rr.remedy_id=r.id WHERE rr.rubric_id=? ORDER BY rr.ordinal,rr.id""", (identifier,))
            result["cross_references"] = self.rows(db, "SELECT * FROM cross_references WHERE rubric_id=? ORDER BY id", (identifier,))
            result["issues"] = self.rows(db, "SELECT * FROM issues WHERE rubric_id=? ORDER BY id", (identifier,))
            result["source_pages"] = self.rows(db, "SELECT pdf_page,printed_page,ocr_confidence,page_type,flags_json FROM pages WHERE pdf_page BETWEEN ? AND ? ORDER BY pdf_page", (row["start_pdf_page"], row["end_pdf_page"]))
            ancestors = []
            parent = row["parent_id"]
            visited = {row["id"]}
            while parent is not None and parent not in visited and len(ancestors) < 100:
                visited.add(parent)
                previous = db.execute("SELECT id,parent_id,label,path FROM rubrics WHERE id=?", (parent,)).fetchone()
                if previous is None:
                    break
                ancestors.append(dict(previous))
                parent = previous["parent_id"]
            result["ancestors"] = list(reversed(ancestors))
        result["children"] = self.children(parent=identifier, limit=5000)
        return result

    def search(self, query, scope="rubrics", limit=40, offset=0, section=None):
        query = str(query).strip()
        if not query:
            return {"items": [], "total": 0, "limit": limit, "offset": offset, "query": query}
        if len(query) > 500:
            raise ValueError("Search text must be 500 characters or fewer.")
        if scope not in ("rubrics", "pages"):
            raise ValueError("Search scope must be rubrics or pages.")
        limit, offset = max(1, min(int(limit), 500)), max(0, int(offset))
        fts = "rubric_search" if scope == "rubrics" else "page_search"
        key = "id" if scope == "rubrics" else "pdf_page"
        # Quote each token: punctuation and FTS syntax in user input remain literal.
        terms = re.findall(r"\w+", query, re.UNICODE)
        expression = " AND ".join('"' + term.replace('"', '""') + '"*' for term in terms)
        section_sql = " AND d.section_id=?" if section is not None else ""
        section_args = [int(section)] if section is not None else []
        with self.connect() as db:
            if scope == "pages" and section is not None and self.has_table(db, "page_sections"):
                section_sql = " AND EXISTS(SELECT 1 FROM page_sections ps WHERE ps.pdf_page=d.pdf_page AND ps.section_id=?)"
            use_fts = bool(expression)
            if use_fts:
                try:
                    total = db.execute(f"SELECT COUNT(*) FROM {fts} JOIN {scope} d ON d.{key}={fts}.rowid WHERE {fts} MATCH ?{section_sql}", [expression] + section_args).fetchone()[0]
                    items = self.rows(db, f"""SELECT d.*,s.name AS section_name FROM {fts}
                             JOIN {scope} d ON d.{key}={fts}.rowid LEFT JOIN sections s ON s.id=d.section_id
                             WHERE {fts} MATCH ?{section_sql} ORDER BY {fts}.rank,d.{key} LIMIT ? OFFSET ?""", [expression] + section_args + [limit, offset])
                except sqlite3.OperationalError:
                    use_fts = False
            if not use_fts:
                value = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
                condition = "(d.path LIKE ? ESCAPE '\\' OR d.text LIKE ? ESCAPE '\\')" if scope == "rubrics" else "d.text LIKE ? ESCAPE '\\'"
                args = [value, value] if scope == "rubrics" else [value]
                total = db.execute(f"SELECT COUNT(*) FROM {scope} d WHERE {condition}{section_sql}", args + section_args).fetchone()[0]
                items = self.rows(db, f"SELECT d.*,s.name AS section_name FROM {scope} d LEFT JOIN sections s ON s.id=d.section_id WHERE {condition}{section_sql} ORDER BY d.{key} LIMIT ? OFFSET ?", args + section_args + [limit, offset])
        return {"items": items, "total": total, "limit": limit, "offset": offset, "query": query, "scope": scope, "method": "fts_prefix" if use_fts else "substring"}

    def remedy(self, query, limit=40, offset=0, exact=False):
        query = str(query).strip()
        if not query:
            return {"items": [], "matches": [], "total": 0, "query": query, "limit": limit, "offset": offset}
        if len(query) > 200:
            raise ValueError("Remedy text must be 200 characters or fewer.")
        limit, offset = max(1, min(int(limit), 500)), max(0, int(offset))
        with self.connect() as db:
            if exact:
                where, args = "(rr.normalized=? COLLATE NOCASE OR rr.raw_token=? COLLATE NOCASE OR m.abbreviation=? COLLATE NOCASE)", [query, query, query]
            else:
                value = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
                where = "(rr.normalized LIKE ? ESCAPE '\\' OR rr.raw_token LIKE ? ESCAPE '\\' OR m.abbreviation LIKE ? ESCAPE '\\' OR m.full_name LIKE ? ESCAPE '\\')"
                args = [value] * 4
            join = "FROM rubric_remedies rr JOIN rubrics r ON r.id=rr.rubric_id LEFT JOIN remedies m ON m.id=rr.remedy_id"
            total = db.execute(f"SELECT COUNT(*) {join} WHERE {where}", args).fetchone()[0]
            items = self.rows(db, f"""SELECT rr.*,r.label,r.path,r.section_id,m.abbreviation,m.full_name {join}
                           WHERE {where} ORDER BY r.order_index,rr.ordinal,rr.id LIMIT ? OFFSET ?""", args + [limit, offset])
            value = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            matches = self.rows(db, "SELECT * FROM remedies WHERE abbreviation LIKE ? ESCAPE '\\' OR full_name LIKE ? ESCAPE '\\' OR normalized LIKE ? ESCAPE '\\' ORDER BY abbreviation LIMIT 100", [value] * 3)
        return {"items": items, "matches": matches, "total": total, "query": query, "limit": limit, "offset": offset, "exact": exact}

    def page(self, number):
        with self.connect() as db:
            row = db.execute("SELECT p.*,s.name AS section_name FROM pages p LEFT JOIN sections s ON s.id=p.section_id WHERE p.pdf_page=?", (int(number),)).fetchone()
            if row is None:
                raise LookupError("Page not found.")
            result = dict(row)
            if self.has_table(db, "page_sections"):
                result["section_regions"] = self.rows(db, """SELECT ps.section_id,s.name,ps.region FROM page_sections ps
                             JOIN sections s ON s.id=ps.section_id WHERE ps.pdf_page=?
                             ORDER BY CASE ps.region WHEN 'top' THEN 0 WHEN 'whole' THEN 1 ELSE 2 END,s.id""", (number,))
            else:
                result["section_regions"] = [{"section_id": row["section_id"], "name": row["section_name"], "region": "whole"}] if row["section_id"] is not None else []
            result["rubrics"] = self.rows(db, "SELECT id,label,path,start_pdf_page,end_pdf_page FROM rubrics WHERE start_pdf_page<=? AND end_pdf_page>=? ORDER BY order_index,id", (number, number))
        return result


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kent repertory · Digital reading room</title>
<style>
[hidden]{display:none!important}
:root{--ink:#20352d;--muted:#687970;--paper:#f6f5ee;--white:#fffefa;--line:#dce2d9;--green:#285c45;--light:#e8efe5;--amber:#8c5d21}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}button,input,select{font:inherit}button,a{touch-action:manipulation}button{cursor:pointer}button:disabled{cursor:default;opacity:.45}a{color:var(--green);text-underline-offset:3px}header{padding:23px 32px 18px;background:var(--green);color:white;display:flex;gap:20px;align-items:center;justify-content:space-between}h1{font:30px/1.15 Georgia,serif;margin:4px 0}header small{letter-spacing:.13em;text-transform:uppercase;font-size:11px;color:#d2e5d3}.header-note{max-width:380px;font-size:12px;color:#e2ece3}.search-bar{display:flex;gap:9px;padding:16px 28px;background:var(--white);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:3}.search-bar input{min-width:80px;flex:1}.search-bar input,.search-bar select{border:1px solid #c7d3c6;border-radius:6px;padding:9px 11px;background:white;color:var(--ink)}.primary{background:var(--green);border:1px solid var(--green);color:white;border-radius:6px;padding:8px 18px}.layout{display:grid;grid-template-columns:310px minmax(0,1fr);min-height:calc(100vh - 180px)}aside{border-right:1px solid var(--line);padding:22px 12px 30px 22px;background:#f0f2e9;max-height:calc(100vh - 173px);overflow:auto;position:sticky;top:75px}main{padding:28px 36px;max-width:1350px;width:100%;min-width:0}.eyebrow{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:650}.nav-title{display:flex;align-items:center;justify-content:space-between;margin:0 8px 12px 0}.quiet{background:transparent;border:0;color:var(--green);padding:3px 5px}.tree{list-style:none;padding:0;margin:0}.tree .tree{padding-left:13px;border-left:1px solid #d4ddcf;margin-left:11px}.tree-row{display:flex;gap:3px;align-items:flex-start;border-radius:5px;padding:2px 0}.tree-row:hover{background:#e5eadf}.toggle{padding:5px 2px;min-width:22px;background:none;border:0;color:var(--muted)}.tree-label{border:0;background:none;text-align:left;color:var(--ink);padding:5px 3px;line-height:1.4;flex:1;font-size:13px;overflow-wrap:anywhere}.tree-label.selected{color:var(--green);font-weight:750;background:#dce9d8;border-radius:4px}.tree-label small{color:var(--muted);font-size:10px;margin-left:5px;font-weight:400}.section-label{font-size:14px;font-weight:650}.tree-more{font-size:12px;margin-left:22px}h2{font:34px/1.25 Georgia,serif;margin:8px 0 16px;overflow-wrap:anywhere}h3{font-size:15px;margin:25px 0 10px}p{margin:10px 0}.intro{max-width:710px;color:var(--muted)}.notice{padding:13px 16px;background:#f5eddc;border:1px solid #e6d8b8;border-radius:6px;color:#72521f;font-size:12px;margin:17px 0}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px;margin:27px 0}.card{background:var(--white);border:1px solid var(--line);padding:18px;border-radius:7px}.card strong{display:block;font:29px Georgia,serif}.card small{color:var(--muted)}.source{display:flex;gap:12px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin:9px 0}.badge{display:inline-block;background:var(--light);border:1px solid #d4dfcf;border-radius:4px;font-size:11px;padding:1px 6px;color:#45614c}.warning{background:#f7edd9;border-color:#e7d5b1;color:#896122}.crumbs{display:flex;gap:5px;flex-wrap:wrap;font-size:12px;color:var(--muted)}.crumbs button{background:none;border:0;color:var(--green);padding:0;font-size:12px}.raw{white-space:pre-wrap;overflow-wrap:anywhere;background:var(--white);border:1px solid var(--line);border-radius:6px;padding:18px;font:14px/1.8 ui-monospace,Consolas,monospace;max-height:420px;overflow:auto}.remedies{display:flex;gap:7px;flex-wrap:wrap}.remedy{background:var(--white);border:1px solid #ced9cb;border-radius:5px;padding:5px 9px;color:var(--green);text-align:left}.remedy small{display:block;font-size:9px;color:var(--muted)}.remedy .grade{font-size:10px;color:var(--amber)}.list{border-top:1px solid var(--line)}.result{padding:15px 0;border-bottom:1px solid var(--line)}.result-title{border:0;background:none;padding:0;color:var(--green);font-weight:650;text-align:left;line-height:1.5;overflow-wrap:anywhere}.result-path{font-size:12px;color:var(--muted);margin:3px 0;overflow-wrap:anywhere}.result-snippet{font-size:13px;color:#58675c;white-space:pre-wrap;max-height:65px;overflow:hidden}.pagination{display:flex;gap:12px;align-items:center;margin:22px 0}.pagination button{padding:6px 14px;border:1px solid #bdcbb9;background:var(--white);border-radius:4px;color:var(--green)}.pagination small{color:var(--muted)}.empty{padding:30px 0;color:var(--muted)}.error{border:1px solid #dcbbb1;color:#883c2d;padding:16px;border-radius:6px}.detail-top{display:flex;justify-content:space-between;gap:12px;align-items:center}.download{font-size:12px;white-space:nowrap}details{margin:18px 0}summary{cursor:pointer;color:var(--muted);font-size:13px}.notes{font-size:12px;color:var(--muted);padding-left:19px}.metadata{font:12px/1.6 ui-monospace,Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere}.loading{color:var(--muted);padding:20px 0}.help{font-size:12px;color:var(--muted);margin-top:22px}.page-lookup{display:flex;gap:7px;margin-top:10px}.page-lookup input{width:105px;padding:5px 7px;border:1px solid #c7d3c6;border-radius:4px;background:white}.page-lookup button{border:1px solid #c7d3c6;background:white;border-radius:4px;color:var(--green)}.check{font-size:12px;display:flex;gap:6px;align-items:center;white-space:nowrap}.muted{color:var(--muted)}
@media(max-width:850px){header{padding:18px}h1{font-size:26px}.header-note{display:none}.search-bar{padding:12px;flex-wrap:wrap}.search-bar input{width:50%}.layout{grid-template-columns:230px minmax(0,1fr)}aside{padding:16px 8px 20px 12px}main{padding:23px 20px}h2{font-size:28px}.cards{grid-template-columns:1fr}.card{padding:12px}.card strong{font-size:25px}}
@media(max-width:580px){.layout{display:block}aside{position:static;max-height:250px;border-right:0;border-bottom:1px solid var(--line)}main{padding:22px 16px}.search-bar select{max-width:155px}.cards{grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.card{padding:9px}.card strong{font-size:22px}.card small{font-size:10px}.detail-top{align-items:flex-start}.search-bar{position:static}}
</style></head><body>
<header><div><small>Digital reading room</small><h1>Kent repertory</h1></div><div class="header-note">An OCR-derived, searchable transcription with a navigable rubric hierarchy. The scanned source remains the reference.</div></header>
<form class="search-bar" id="searchForm"><input id="searchInput" type="search" placeholder="Search symptoms, rubric paths, or remedies…" aria-label="Search repertory" autocomplete="off"><select id="searchMode" aria-label="Search mode"><option value="rubrics">Rubric search</option><option value="remedy">Remedy lookup</option><option value="pages">Full page text</option></select><label class="check" id="exactLabel" hidden><input id="exactRemedy" type="checkbox">Exact</label><button class="primary">Search</button></form>
<div class="layout"><aside><div class="nav-title"><span class="eyebrow">Browse the repertory</span><button class="quiet" id="homeButton">Overview</button></div><ul class="tree" id="sectionTree"></ul><div class="help">Open a section, then expand its rubrics. Indentation represents the inferred parent–child relationship.</div><form class="page-lookup" id="pageForm"><input id="pageInput" type="number" min="1" placeholder="PDF page" aria-label="PDF page number"><button>Open page</button></form></aside><main id="main" aria-live="polite"><div class="loading">Opening the repertory…</div></main></div>
<script>
'use strict';
const $=id=>document.getElementById(id), main=$('main');
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=value=>Number(value||0).toLocaleString();
let sections=[],stats=null,requestSerial=0;
async function api(path){const res=await fetch(path);let data;try{data=await res.json()}catch(e){throw Error('The local server did not return readable data.')}if(!res.ok)throw Error(data.error||res.statusText);return data}
function sourceLink(page,label){return `<a href="/source.pdf#page=${Number(page)||1}" target="_blank" rel="noopener">${esc(label||'View source PDF · page '+page)}</a>`}
function flagList(value){if(!value)return [];try{const v=typeof value==='string'?JSON.parse(value):value;return Array.isArray(v)?v:Object.keys(v).map(k=>k+': '+v[k])}catch(e){return [String(value)]}}
function gradeLabel(r){if(r.grade!==null&&r.grade!==undefined)return 'Reviewed grade '+r.grade;if(r.grade_candidate!==null&&r.grade_candidate!==undefined)return ({1:'Capital type',2:'Italic type',3:'Roman type'}[r.grade_candidate]||'Type '+r.grade_candidate)+' · inferred';return 'Grade unreviewed'}
function crossReference(c){const printed=Number(c.target_printed_page),offset=Number(stats.metadata.printed_page_offset??46),pdfPage=printed+offset;const hasPage=c.target_printed_page!==null&&c.target_printed_page!==undefined&&Number.isInteger(printed)&&printed>0&&Number.isInteger(pdfPage)&&pdfPage>0&&(!stats.metadata.source_pdf_pages||pdfPage<=stats.metadata.source_pdf_pages);return `<div class="result">${c.target_rubric_id?`<button class="result-title" data-node="${c.target_rubric_id}">${esc(c.text)}</button>`:esc(c.text)} <span class="badge">${esc(c.status||'unresolved')}</span>${c.target_printed_page!==null&&c.target_printed_page!==undefined?`<div class="result-path">Target printed page: ${esc(c.target_printed_page)}</div>`:''}${hasPage?`<div class="source">${sourceLink(pdfPage,'View referenced scan · PDF page '+pdfPage)}<button class="quiet" data-page="${pdfPage}">Read referenced page text</button></div>`:''}</div>`}
function navigate(hash){if(location.hash===hash)route();else location.hash=hash}
function bindActions(root=main){root.querySelectorAll('[data-node]').forEach(el=>el.onclick=()=>navigate('#node/'+el.dataset.node));root.querySelectorAll('[data-page]').forEach(el=>el.onclick=()=>navigate('#page/'+el.dataset.page));root.querySelectorAll('[data-remedy]').forEach(el=>el.onclick=()=>{ $('searchInput').value=el.dataset.remedy;$('searchMode').value='remedy';$('exactRemedy').checked=true;setMode();submitSearch()});root.querySelectorAll('[data-section]').forEach(el=>el.onclick=()=>navigate('#section/'+el.dataset.section))}
function listNode(r){return `<div class="result"><button class="result-title" data-node="${r.id}">${esc(r.label)}</button><div class="result-path">${esc(r.path)}</div><div class="source"><span>PDF ${r.start_pdf_page}${r.end_pdf_page&&r.end_pdf_page!==r.start_pdf_page?'–'+r.end_pdf_page:''}</span>${r.remedy_count!==undefined?`<span>${fmt(r.remedy_count)} remedy entries</span>`:''}${r.hierarchy_status?`<span>${esc(r.hierarchy_status)}</span>`:''}</div></div>`}
async function loadTreeChildren(container,section,parent,offset=0){const params=new URLSearchParams({limit:'300',offset:String(offset)});params.set(parent!==null?'parent':'section',parent!==null?parent:section);const data=await api('/api/children?'+params);data.items.forEach(r=>container.append(treeItem(r,section)));if(data.offset+data.items.length<data.total){const li=document.createElement('li'),btn=document.createElement('button');btn.className='quiet tree-more';btn.textContent='Load more rubrics…';btn.onclick=async()=>{btn.disabled=true;try{await loadTreeChildren(container,section,parent,offset+data.items.length);li.remove()}catch(e){btn.textContent=e.message;btn.disabled=false}};li.append(btn);container.append(li)}}
function treeItem(r,section,isSection=false){const li=document.createElement('li'),row=document.createElement('div'),toggle=document.createElement('button'),label=document.createElement('button'),children=document.createElement('ul');row.className='tree-row';toggle.className='toggle';toggle.setAttribute('aria-label','Expand '+(r.name||r.label));toggle.setAttribute('aria-expanded','false');toggle.textContent=(isSection||r.has_children)?'▸':'·';toggle.disabled=!(isSection||r.has_children);label.className='tree-label'+(isSection?' section-label':'');label.textContent=isSection?r.name:r.label;label.title=isSection?r.name:r.path;label.onclick=()=>navigate(isSection?'#section/'+r.id:'#node/'+r.id);children.className='tree';children.hidden=true;let loaded=false;toggle.onclick=async()=>{if(!children.hidden){children.hidden=true;toggle.textContent='▸';toggle.setAttribute('aria-expanded','false');return}toggle.disabled=true;try{if(!loaded){await loadTreeChildren(children,section,isSection?null:r.id);loaded=true}children.hidden=false;toggle.textContent='▾';toggle.setAttribute('aria-expanded','true')}catch(e){showError(e)}finally{toggle.disabled=false}};row.append(toggle,label);li.append(row,children);return li}
function showError(error){main.innerHTML=`<div class="error">${esc(error.message||error)}</div>`}
function overview(){main.innerHTML=`<span class="eyebrow">From printed pages to connected entries</span><h2>A repertory you can navigate.</h2><p class="intro">Follow a section through its nested rubrics, search the complete page text, or look up a remedy to find its recorded occurrences. Every entry links back to its scanned page.</p><div class="cards"><div class="card"><strong>${fmt(stats.rubrics)}</strong><small>rubric nodes</small></div><div class="card"><strong>${fmt(stats.rubric_remedies)}</strong><small>remedy occurrences</small></div><div class="card"><strong>${fmt(stats.pages)}</strong><small>source PDF pages</small></div></div><div class="notice"><strong>Transcription status: OCR-derived and unreviewed.</strong> Text, remedy recognition, hierarchy, and inferred type styles may contain errors. Check the source page before relying on an entry. Inferred type styles are not reviewed grades.</div><h3>Three ways to explore</h3><p><strong>Browse:</strong> expand a section in the left panel to follow the rubric hierarchy.</p><p><strong>Search:</strong> enter words from a symptom or rubric. Rubric search matches word prefixes across the path and text; full page search includes the surrounding transcription.</p><p><strong>Remedy lookup:</strong> enter an abbreviation or full name. Select Exact for a specific normalized abbreviation. Occurrences retain their raw OCR token.</p><p class="help">PDF page numbers count from the first PDF page. Printed page labels, where available, are shown separately. All data stays on this computer; this browser uses a local, read-only database.</p><details><summary>Dataset details and extraction metadata</summary><pre class="metadata">${esc(JSON.stringify(stats.metadata,null,2))}</pre><p class="muted">${fmt(stats.issues)} recorded extraction issues · ${fmt(stats.reviewed_grades)} reviewed grades · ${fmt(stats.candidate_grades)} inferred type styles</p></details>${stats.source_available?'':'<div class="notice">The original PDF is not at its recorded location. Restart with <code>--source "path/to/file.pdf"</code> to restore source links.</div>'}`}
function pagination(data,action){const shown=data.items.length;if(!data.total)return '';return `<div class="pagination"><button id="prevPage" ${data.offset===0?'disabled':''}>Previous</button><small>${fmt(data.offset+1)}–${fmt(data.offset+shown)} of ${fmt(data.total)}</small><button id="nextPage" ${data.offset+shown>=data.total?'disabled':''}>Next</button></div>`}
function bindPagination(data,go){const prev=$('prevPage'),next=$('nextPage');if(prev)prev.onclick=()=>go(Math.max(0,data.offset-data.limit));if(next)next.onclick=()=>go(data.offset+data.limit)}
async function sectionView(id,serial){const s=sections.find(s=>String(s.id)===String(id));if(!s)throw Error('Section not found.');const data=await api('/api/children?section='+id+'&limit=5000');if(serial!==requestSerial)return;main.innerHTML=`<span class="eyebrow">${esc(s.group_name||'Repertory section')}</span><h2>${esc(s.name)}</h2><div class="source"><span>${fmt(s.rubric_count)} rubrics in this section</span><span>Printed pages ${esc(s.printed_start??'?')}–${esc(s.printed_end??'?')}</span>${sourceLink(s.pdf_start)}</div><h3>Top-level rubrics</h3><div class="list">${data.items.map(listNode).join('')||'<p class="empty">No top-level rubrics recorded.</p>'}</div>${data.total>data.items.length?'<p class="notice">More rubrics are available through the paginated tree or command-line interface.</p>':''}`;bindActions()}
async function nodeView(id,serial){const r=await api('/api/node/'+id);if(serial!==requestSerial)return;const flags=flagList(r.flags_json);const pages=r.source_pages||[];main.innerHTML=`<div class="detail-top"><span class="eyebrow">Rubric ${r.id}</span><a class="download" href="/api/node/${r.id}" target="_blank">Open JSON</a></div><div class="crumbs"><button data-section="${r.section_id}">${esc(r.section.name)}</button>${r.ancestors.map(a=>`<span>›</span><button data-node="${a.id}">${esc(a.label)}</button>`).join('')}</div><h2>${esc(r.label)}</h2><div class="source">${sourceLink(r.start_pdf_page)}${r.end_pdf_page!==r.start_pdf_page?sourceLink(r.end_pdf_page,'Last source page · '+r.end_pdf_page):''}<span>Printed ${pages.map(p=>esc(p.printed_page??'?')).join(', ')||'unrecorded'}</span><span class="badge">Hierarchy: ${esc(r.hierarchy_status||'unreviewed')}</span></div>${flags.length?`<div class="notice">Extraction flags: ${flags.map(esc).join(' · ')}</div>`:''}<h3>Remedies <span class="muted">(${fmt(r.remedies.length)})</span></h3><div class="remedies">${r.remedies.map(m=>`<button class="remedy" data-remedy="${esc(m.normalized||m.abbreviation||m.raw_token)}" title="${esc(m.full_name||m.grade_basis||'Raw OCR token')}" ><span>${esc(m.raw_token)}</span><small class="grade">${esc(gradeLabel(m))}</small></button>`).join('')||'<p class="muted">No remedy tokens extracted for this rubric.</p>'}</div><p class="help">Remedy tokens preserve OCR text. Type styles shown as “inferred” require comparison with the scan; unknown or ambiguous grades are left unset.</p><h3>Rubric transcription</h3><div class="raw">${esc(r.text||'No text recorded.')}</div>${r.cross_references.length?`<h3>Cross-references</h3><div class="list">${r.cross_references.map(crossReference).join('')}</div>`:''}<h3>Subrubrics <span class="muted">(${fmt(r.children.total)})</span></h3><div class="list">${r.children.items.map(listNode).join('')||'<p class="muted">This is a leaf rubric.</p>'}</div><details><summary>Provenance and recorded issues</summary><p class="help">Section ID ${r.section_id} · Parent ${r.parent_id??'none'} · Depth ${r.depth} · Source line ${r.start_line_id??'unknown'}</p><ul class="notes">${r.issues.map(i=>`<li>${esc(i.kind)}: ${esc(i.detail)}</li>`).join('')||'<li>No rubric-specific issue recorded. This does not indicate manual verification.</li>'}</ul><pre class="metadata">${esc(JSON.stringify(pages,null,2))}</pre></details>`;bindActions()}
async function pageView(id,serial){const p=await api('/api/page/'+id);if(serial!==requestSerial)return;const regions=p.section_regions||[];main.innerHTML=`<span class="eyebrow">${esc(regions.map(s=>s.name).join(' / ')||p.section_name||p.page_type||'Source document')}</span><h2>PDF page ${p.pdf_page}</h2><div class="source"><span>Printed page ${esc(p.printed_page??'unrecorded')}</span>${sourceLink(p.pdf_page)}<span>OCR confidence: ${esc(p.ocr_confidence??'unrecorded')}</span><a href="/api/page/${p.pdf_page}" target="_blank">Open JSON</a></div>${regions.length?`<div class="source">${regions.map(s=>`<button class="quiet" data-section="${s.section_id}">${esc(s.name)} · ${esc(s.region==='whole'?'whole page':s.region+' of page')}</button>`).join('')}</div>`:''}<div class="pagination"><button id="prevSource" ${p.pdf_page<=1?'disabled':''}>Previous page</button><button id="nextSource" ${p.pdf_page>=(stats.metadata.source_pdf_pages||stats.pages)?'disabled':''}>Next page</button></div><h3>Page transcription</h3><div class="raw" style="max-height:none">${esc(p.text||'No text recorded.')}</div><h3>Rubrics on this page</h3><div class="list">${p.rubrics.map(listNode).join('')||'<p class="muted">No rubric nodes recorded for this page.</p>'}</div><details><summary>Page extraction flags</summary><pre class="metadata">${esc(JSON.stringify(flagList(p.flags_json),null,2))}</pre></details>`;bindActions();$('prevSource').onclick=()=>navigate('#page/'+(p.pdf_page-1));$('nextSource').onclick=()=>navigate('#page/'+(p.pdf_page+1))}
function searchHash(q,mode,offset,exact){return '#search/'+new URLSearchParams({q,mode,offset:String(offset||0),exact:exact?'1':'0'})}
async function searchView(params,serial){const q=params.get('q')||'',mode=params.get('mode')||'rubrics',offset=Number(params.get('offset')||0),exact=params.get('exact')==='1';$('searchInput').value=q;$('searchMode').value=mode;$('exactRemedy').checked=exact;setMode();const endpoint=mode==='remedy'?'/api/remedy?':'/api/search?';const query=new URLSearchParams({q,scope:mode,limit:'40',offset:String(offset),exact:exact?'1':'0'});const data=await api(endpoint+query);if(serial!==requestSerial)return;let content='';if(mode==='remedy'){content=data.items.map(r=>`<div class="result"><button class="result-title" data-node="${r.rubric_id}">${esc(r.path)}</button><div class="source"><strong>${esc(r.raw_token)}</strong><span>${esc(r.full_name||r.abbreviation||r.normalized||'Unmatched token')}</span><span class="badge warning">${esc(gradeLabel(r))}</span>${sourceLink(r.pdf_page,'PDF page '+r.pdf_page)}</div></div>`).join('')}else if(mode==='pages'){content=data.items.map(p=>`<div class="result"><button class="result-title" data-page="${p.pdf_page}">PDF page ${p.pdf_page} · Printed ${esc(p.printed_page??'?')}</button><div class="result-path">${esc(p.section_name||p.page_type||'')}</div><div class="result-snippet">${esc(snippet(p.text,q))}</div></div>`).join('')}else{content=data.items.map(r=>`<div class="result"><button class="result-title" data-node="${r.id}">${esc(r.path||r.label)}</button><div class="result-path">PDF ${r.start_pdf_page} · ${esc(r.section_name||'')}</div><div class="result-snippet">${esc(snippet(r.text,q))}</div></div>`).join('')}main.innerHTML=`<span class="eyebrow">${mode==='remedy'?'Remedy occurrences':mode==='pages'?'Full page text':'Rubric search'}</span><h2>${esc(q)}</h2><p class="muted">${fmt(data.total)} ${mode==='remedy'?'occurrences':'results'}${exact&&mode==='remedy'?' · exact abbreviation match':''}</p>${mode==='remedy'&&data.matches.length?`<details><summary>${data.matches.length} matching remedy glossary entries</summary><div class="remedies">${data.matches.map(r=>`<button class="remedy" data-remedy="${esc(r.normalized||r.abbreviation)}">${esc(r.abbreviation)}<small>${esc(r.full_name||'')}</small></button>`).join('')}</div></details>`:''}<div class="list">${content||'<p class="empty">No results. Try a shorter spelling or search full page text; OCR can alter words and remedy abbreviations.</p>'}</div>${pagination(data)}`;bindActions();bindPagination(data,next=>navigate(searchHash(q,mode,next,exact)))}
function snippet(text,query){text=String(text||'');const word=(query.match(/\w+/)||[''])[0],index=text.toLowerCase().indexOf(word.toLowerCase());const start=Math.max(0,index-80);return (start?'…':'')+text.slice(start,start+350)+(text.length>start+350?'…':'')}
function setMode(){$('exactLabel').hidden=$('searchMode').value!=='remedy'}
function submitSearch(){const q=$('searchInput').value.trim();if(q)navigate(searchHash(q,$('searchMode').value,0,$('exactRemedy').checked))}
async function route(){const serial=++requestSerial;main.innerHTML='<div class="loading">Loading…</div>';const hash=location.hash.slice(1),parts=hash.split('/');try{if(parts[0]==='node')await nodeView(parts[1],serial);else if(parts[0]==='section')await sectionView(parts[1],serial);else if(parts[0]==='page')await pageView(parts[1],serial);else if(parts[0]==='search')await searchView(new URLSearchParams(hash.slice(7)),serial);else overview()}catch(e){if(serial===requestSerial)showError(e)}window.scrollTo({top:0,behavior:'instant'})}
$('searchForm').onsubmit=e=>{e.preventDefault();submitSearch()};$('searchMode').onchange=setMode;$('homeButton').onclick=()=>navigate('#');$('pageForm').onsubmit=e=>{e.preventDefault();const value=Number($('pageInput').value);if(value>0)navigate('#page/'+value)};document.addEventListener('keydown',e=>{if(e.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)){e.preventDefault();$('searchInput').focus()}});window.addEventListener('hashchange',()=>{if(stats)route()});
(async()=>{try{[stats,sections]=await Promise.all([api('/api/stats'),api('/api/sections')]);sections.forEach(s=>$('sectionTree').append(treeItem(s,s.id,true)));setMode();await route()}catch(e){showError(e)}})();
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    server_version = "KentReader/1.0"

    @property
    def repertory(self):
        return self.server.repertory

    def log_message(self, fmt, *args):
        # Search text and source paths are not written to request logs.
        if len(args) > 1 and str(args[1]).isdigit() and int(args[1]) >= 500:
            super().log_message("Server error %s on %s", args[1], urlsplit(self.path).path)

    def common_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")

    def output(self, value, status=200, content_type="application/json; charset=utf-8", head=False):
        body = (json.dumps(value, ensure_ascii=False) if content_type.startswith("application/json") else value).encode("utf-8")
        self.send_response(status)
        self.common_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if content_type.startswith("text/html"):
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def do_HEAD(self):
        self.handle_read(head=True)

    def do_GET(self):
        self.handle_read()

    def handle_read(self, head=False):
        try:
            # Avoid serving database data to a DNS-rebinding origin.
            hostname = urlsplit("http://" + self.headers.get("Host", "")).hostname
            if hostname not in ("127.0.0.1", "localhost", "::1"):
                self.output({"error": "This reader accepts localhost requests only."}, status=403, head=head)
                return
            request = urlsplit(self.path)
            path = unquote(request.path)
            if path in ("/", "/index.html"):
                self.output(HTML, content_type="text/html; charset=utf-8", head=head)
                return
            if path == "/source.pdf":
                self.send_pdf(head)
                return
            if path == "/favicon.ico":
                self.output("", status=204, content_type="text/plain", head=head)
                return
            parameters = parse_qs(request.query)
            one = lambda name, default=None: parameters.get(name, [default])[0]
            integer = lambda name, default=None: int(one(name, default)) if one(name, default) is not None else None
            if path == "/api/stats":
                value = self.repertory.stats()
            elif path == "/api/sections":
                value = self.repertory.sections()
            elif path == "/api/children":
                value = self.repertory.children(section=integer("section"), parent=integer("parent"), limit=integer("limit", 1000), offset=integer("offset", 0))
            elif path.startswith("/api/node/"):
                value = self.repertory.node(int(path.rsplit("/", 1)[1]))
            elif path == "/api/search":
                value = self.repertory.search(one("q", ""), scope=one("scope", "rubrics"), limit=integer("limit", 40), offset=integer("offset", 0), section=integer("section"))
            elif path == "/api/remedy":
                value = self.repertory.remedy(one("q", ""), limit=integer("limit", 40), offset=integer("offset", 0), exact=one("exact") == "1")
            elif path.startswith("/api/page/"):
                value = self.repertory.page(int(path.rsplit("/", 1)[1]))
            else:
                self.output({"error": "Not found."}, status=404, head=head)
                return
            self.output(value, head=head)
        except (ValueError, TypeError) as error:
            self.output({"error": str(error)}, status=400, head=head)
        except (LookupError, FileNotFoundError) as error:
            self.output({"error": str(error)}, status=404, head=head)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as error:
            self.output({"error": "Unable to read the repertory: " + str(error)}, status=500, head=head)

    def send_pdf(self, head=False):
        source = self.repertory.source_path()
        if not source or not source.is_file():
            self.output({"error": "The original source PDF is unavailable. Restart viewer.py with --source followed by its path."}, status=404, head=head)
            return
        size = source.stat().st_size
        start, end, status = 0, size - 1, 200
        requested = self.headers.get("Range")
        if requested:
            match = re.fullmatch(r"bytes=(\d*)-(\d*)", requested.strip())
            if not match or not any(match.groups()):
                self.send_response(416)
                self.common_headers()
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            left, right = match.groups()
            if left:
                start = int(left)
                end = min(int(right), size - 1) if right else size - 1
            else:
                suffix = int(right)
                start, end = max(0, size - suffix), size - 1
            if start > end or start >= size:
                self.send_response(416)
                self.common_headers()
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            status = 206
        self.send_response(status)
        self.common_headers()
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Content-Disposition", "inline; filename=kent_source.pdf")
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if not head:
            with source.open("rb") as stream:
                stream.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk = stream.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--source", type=Path, help="Override the original PDF path recorded in metadata.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    repertory = Repertory(args.database, args.source)
    try:
        repertory.stats()
    except (OSError, sqlite3.Error) as error:
        parser.exit(1, f"Cannot open the repertory: {error}\n")
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    except OSError:
        if args.port != 8765:
            raise
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.repertory = repertory
    server.daemon_threads = True
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"Kent repertory reader: {url}\nDatabase: {repertory.database}\nRead-only; available on this computer only. Press Ctrl+C to stop.", flush=True)
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nReader stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
