'use client';
import { useState } from 'react';
import { API_BASE } from '@/lib/api';

export default function Page() {
  const [file, setFile] = useState<File| null>(null);
  const [msg, setMsg] = useState<string>('');
  const [busy, setBusy] = useState<boolean>(false);

  async function onUpload() {
    if (!file) return;
    setBusy(true); setMsg('');
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: fd });
    setBusy(false);
    if (res.redirected) {
      window.location.href = '/gallery' + (new URL(res.url)).search;
      return;
    }
    if (res.ok) setMsg('Uploaded.'); else setMsg('Upload failed.');
  }

  return (
    <div className="panel">
      <h1>Upload a Video</h1>
      <p className="muted">Saves to server and extracts frames every 10th frame.</p>
      <div className="card" style={{display:'grid',gap:12}}>
        <input type="file" accept="video/*" onChange={e=>setFile(e.target.files?.[0]||null)} />
        <button className="btn primary" onClick={onUpload} disabled={!file||busy}>{busy?'Uploading...':'Upload & Extract'}</button>
        {msg && <div className="muted">{msg}</div>}
      </div>
    </div>
  );
}


