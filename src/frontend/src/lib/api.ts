// src/lib/api.ts
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export async function embedApi(params: {
  carrier: File;
  payload: File;
  bitsPerFrame: number;
  key: string;
  vigenere: boolean;
}) {
  const fd = new FormData();
  fd.append("carrier", params.carrier);
  fd.append("payload", params.payload);
  fd.append("bits_per_frame", String(params.bitsPerFrame));
  fd.append("key", params.key);
  fd.append("vigenere", String(params.vigenere));

  const res = await fetch(`${API_BASE}/api/embed`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(await res.text());

  const psnrHeader = res.headers.get("X-PSNR-dB");
  const psnr = psnrHeader ? Number(psnrHeader) : NaN;

  const blob = await res.blob();
  // Prefer a friendly filename; make sure it ends with .mp3
  const name = `stego_${params.carrier.name.endsWith(".mp3") ? params.carrier.name : params.carrier.name + ".mp3"}`;
  const stegoFile = new File([blob], name, { type: "audio/mpeg" });

  return {
    stegoFile,
    psnr,
    stegoSize: blob.size,
  };
}

export async function extractApi(params: {
  stego: File;
  bitsPerFrame: number;
  key: string;
  vigenere: boolean;
  saveAs?: string; // optional preferred filename (without extension)
}) {
  const fd = new FormData();
  fd.append("stego", params.stego);
  fd.append("bits_per_frame", String(params.bitsPerFrame));
  fd.append("key", params.key);
  fd.append("vigenere", String(params.vigenere));

  const res = await fetch(`${API_BASE}/api/extract`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(await res.text());

  const ext = res.headers.get("X-Ext") || "";
  const ct = res.headers.get("Content-Type") || "application/octet-stream";
  const blob = await res.blob();

  const base = params.saveAs?.trim() || "extracted";
  const finalName = ext && !base.includes(".") ? `${base}.${ext}` : base;

  const file = new File([blob], finalName, { type: ct });

  return {
    file,
    filename: file.name,
    size: blob.size,
    contentType: ct,
  };
}

export async function capacityApi(params: {
  carrier: File;
  bitsPerFrame: number;
  payloadSize?: number;   // optional
  vigenere: boolean;      // echoed back by server (doesn't affect capacity)
}) {
  const fd = new FormData();
  fd.append("carrier", params.carrier);
  fd.append("bits_per_frame", String(params.bitsPerFrame));
  fd.append("vigenere", String(params.vigenere));
  if (typeof params.payloadSize === "number") {
    fd.append("payload_size", String(params.payloadSize));
  }

  const res = await fetch(`${API_BASE}/api/capacity`, { method: "POST", body: fd });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as {
    ok: boolean;
    bits_per_frame: number;
    vigenere: boolean;
    capacity_bits: number;
    capacity_bytes: number;
    header_size_bytes: number;
    usable_payload_bytes: number;
    payload_size?: number;
    fits?: boolean;
  };
}