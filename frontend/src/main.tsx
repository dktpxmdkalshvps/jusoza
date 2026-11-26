import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
type Preview = { columns: string[]; row_count: number; preview: unknown[][]; max_rows: number };
function App() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [column, setColumn] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  async function submit(path: string, body: FormData) {
    const response = await fetch(API + path, { method: "POST", body });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(typeof payload.detail === "string" ? payload.detail : "서버 요청에 실패했습니다.");
    }
    return response;
  }
  async function inspect(next: File) {
    setFile(next); setPreview(null); setColumn(""); setDone(false); setError(""); setBusy(true);
    try {
      const body = new FormData(); body.append("file", next);
      const data: Preview = await (await submit("/api/columns", body)).json();
      setPreview(data);
      const guess = data.columns.find(x => /도로명|주소|address/i.test(x));
      setColumn(guess || data.columns[0] || "");
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  async function convert() {
    if (!file || !column) return;
    setBusy(true); setError(""); setDone(false);
    try {
      const body = new FormData(); body.append("file", file); body.append("address_column", column);
      const response = await submit("/api/convert", body);
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = "jusoza_result.xlsx"; anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      setDone(true);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }
  return <main className="shell">
    <header><div className="brand">Jusoza<span>.</span></div><div className="eyebrow">공식 주소 데이터 기반</div></header>
    <section className="hero"><span className="tag">ADDRESS STANDARDIZATION</span><h1>엑셀 속 주소를<br/><em>공식 주소로 정리하세요.</em></h1>
      <p>주소가 들어 있는 엑셀 또는 CSV를 업로드하면 행정안전부 주소 API로 조회한 도로명·지번·영문주소를 새로운 열로 추가합니다.</p></section>
    <section className="panel"><div className="step">01 <span>파일 선택</span></div>
      <label className="drop"><input type="file" accept=".xlsx,.csv" onChange={e => { const f=e.target.files?.[0]; if(f) void inspect(f); }} />
        <strong>{file ? file.name : "엑셀 또는 CSV 파일을 선택하세요"}</strong><small>현재 MVP는 최대 30행 · 3MB · CSV UTF-8 지원</small></label>
      {preview && <><div className="step">02 <span>주소 컬럼 선택</span></div><label className="field">변환할 주소가 들어 있는 열
        <select value={column} onChange={e=>setColumn(e.target.value)}>{preview.columns.map((x,i)=><option key={i} value={x}>{x}</option>)}</select></label>
        <div className="meta">{preview.row_count}개 데이터 행 감지</div>
        <div className="tablewrap"><table><thead><tr>{preview.columns.map((x,i)=><th key={i}>{x}</th>)}</tr></thead><tbody>
          {preview.preview.map((r,i)=><tr key={i}>{r.map((v,j)=><td key={j}>{String(v ?? "")}</td>)}</tr>)}
        </tbody></table></div>
        <div className="step">03 <span>변환 결과 다운로드</span></div>
        <button disabled={busy || !column} onClick={()=>void convert()}>{busy ? "처리 중..." : "공식 주소 조회 후 엑셀 받기"}</button>
        <p className="note">주소 검색 결과가 1건일 때만 자동 기입합니다. 복수 후보·미검색·API 오류는 상태값으로 남기며 원본은 유지됩니다.</p></>}
      {busy && <p role="status">요청을 처리하고 있습니다. 창을 닫지 마세요.</p>}
      {error && <p className="error" role="alert">{error}</p>}
      {done && <p className="success" role="status">결과 엑셀 다운로드를 시작했습니다.</p>}
    </section><footer>Jusoza MVP · 주소의 공식 표준화는 실제 사업장 위치 또는 운영 여부의 검증과 다릅니다.</footer>
  </main>;
}
createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
