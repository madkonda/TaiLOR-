'use client';
import { useEffect, useState } from 'react';
import { absoluteBackendUrl, API_BASE } from '@/lib/api';

export default function Gallery() {
  const [video, setVideo] = useState<string>('');
  const [videos, setVideos] = useState<string[]>([]);
  const [frames, setFrames] = useState<string[]>([]);

  useEffect(() => {
    // naive: backend exposes /videos listing via UI only; prompt user to type basename
  }, []);

  async function loadFrames(v: string) {
    setVideo(v);
    setFrames([]);
    if (!v) return;
    const res = await fetch(`${API_BASE}/api/frames?video=${encodeURIComponent(v)}`);
    const data = await res.json();
    const urls = (data.frames || []).map((p: string) => absoluteBackendUrl(p));
    setFrames(urls);
  }

  return (
    <div className="panel" style={{display:'grid',gap:12}}>
      <h1>Frames Gallery</h1>
      <div className="card" style={{display:'flex',gap:10,alignItems:'center'}}>
        <label>Video basename</label>
        <input placeholder="e.g. myvideo" value={video} onChange={e=>setVideo(e.target.value)} />
        <button className="btn" onClick={()=>loadFrames(video)}>Load</button>
      </div>
      <div className="grid col3">
        {frames.map((src, i)=>(
          <a key={i} href={src} target="_blank" rel="noreferrer" className="card">
            <img src={src} alt="frame" className="img" />
          </a>
        ))}
      </div>
    </div>
  );
}


