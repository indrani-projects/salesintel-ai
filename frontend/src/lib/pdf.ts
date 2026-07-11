import html2pdf from "html2pdf.js";

export async function downloadElementAsPdf(
  element: HTMLElement,
  filename: string,
): Promise<void> {
  await html2pdf()
    .set({
      margin: [12, 12, 12, 12],
      filename,
      image: { type: "jpeg", quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
      jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
    })
    .from(element)
    .save();
}

export function safeFilename(name: string): string {
  return name.replace(/[^\w.-]+/g, "_").replace(/_+/g, "_").slice(0, 80);
}
