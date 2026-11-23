import React from "react";
import { createRoot } from "react-dom/client";

function App() {
  return <main style={{maxWidth: 720, margin: "64px auto", fontFamily: "sans-serif"}}>
    <h1>jusoza</h1>
    <p>행정안전부 주소정보 기반 엑셀 주소 현행화 서비스</p>
    <p>초기 스캐폴드입니다. 업로드 및 작업 처리 API는 다음 단계에서 연결합니다.</p>
  </main>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
