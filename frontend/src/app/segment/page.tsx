'use client';
import { useEffect, useRef, useState } from 'react';
import { absoluteBackendUrl, API_BASE } from '@/lib/api';

export default function Segment() {
  const [video, setVideo] = useState('');
  const [frames, setFrames] = useState<string[]>([]);
  const [selected, setSelected] = useState<string>('');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [imgObj, setImgObj] = useState<HTMLImageElement | null>(null);
  const [pts, setPts] = useState<{x:number,y:number}[]>([]);
  const [msg, setMsg] = useState('');

  async function loadFrames(v: string) {
    setVideo(v);
    setPts([]);
    setSelected('');
    if (!v) return setFrames([]);
    const res = await fetch(`${API_BASE}/api/frames?video=${encodeURIComponent(v)}`);
    const data = await res.json();
    const urls = (data.frames || []).map((p: string) => absoluteBackendUrl(p));
    setFrames(urls);
  }

  function openImage(src: string) {
    setSelected(src);
    const img = new Image();
    img.onload = () => {
      const c = canvasRef.current;
      if (!c) return;
      c.width = img.width; c.height = img.height;
      const ctx = c.getContext('2d');
      if (!ctx) return;
      ctx.clearRect(0,0,c.width,c.height);
      ctx.drawImage(img,0,0);
      setPts([]);
      setImgObj(img);
    };
    img.src = src;
  }

  function onCanvasClick(e: React.MouseEvent<HTMLCanvasElement>) {
    if (!canvasRef.current || !imgObj) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = Math.round(e.clientX - rect.left);
    const y = Math.round(e.clientY - rect.top);
    const next = [...pts, {x,y}].slice(-2);
    setPts(next);

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(imgObj, 0, 0);
    ctx.fillStyle = '#22d3ee';
    next.forEach(p=>{ ctx.beginPath(); ctx.arc(p.x,p.y,5,0,Math.PI*2); ctx.fill(); });
  }

  async function runSegmentation() {
    if (!selected || pts.length<2) return;
    setMsg('Starting segmentation...');
    const form = new FormData();
    form.append('video', video);
    const rel = selected.replace(/^https?:\/\/[^/]+/, '');
    form.append('frame', rel);
    form.append('x1', String(pts[0].x));
    form.append('y1', String(pts[0].y));
    form.append('x2', String(pts[1].x));
    form.append('y2', String(pts[1].y));
    const res = await fetch(`${API_BASE}/api/segment`, { method:'POST', body: form, redirect:'follow' });
    if (res.redirected) window.location.href = res.url; else setMsg(res.ok?'Segmentation requested.':'Failed to request segmentation');
  }

  return (
    <div className="panel" style={{display:'grid',gap:12}}>
      <h1>SAM2 Segmentation</h1>
      <div className="card" style={{display:'flex',gap:10,alignItems:'center'}}>
        <label>Video basename</label>
        <input placeholder="e.g. myvideo" value={video} onChange={e=>setVideo(e.target.value)} />
        <button className="btn" onClick={()=>loadFrames(video)}>Load</button>
      </div>
      <div className="grid col3">
        {frames.map((src,i)=> (
          <a key={i} href="#" onClick={(e)=>{e.preventDefault(); openImage(src);}} className="card">
            <img src={src} className="img" alt="frame" />
          </a>
        ))}
      </div>

      <div className="card" style={{display:'grid',gap:8}}>
        <div className="muted">Click two points on the image</div>
        <canvas ref={canvasRef} onClick={onCanvasClick} style={{maxWidth:'100%'}} />
        <div className="muted">Points: {pts.map(p=>`(${p.x},${p.y})`).join(' , ')|| '-'}</div>
        <button className="btn primary" disabled={!selected||pts.length<2} onClick={runSegmentation}>Run Segmentation</button>
        {msg && <div className="muted">{msg}</div>}
      </div>
    </div>
  );
}


