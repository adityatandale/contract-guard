export const metadata = { title: "Contract Guard" };
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, background: "#f6f7f9", color: "#1a1a1a" }}>
        {children}
      </body>
    </html>
  );
}
