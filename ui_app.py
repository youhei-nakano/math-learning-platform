import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from math_research_workflow import WorkflowError, run_workflow


MAX_REQUEST_BYTES = 10_000


def render_page(content="質問を入力してください。", question=""):
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Math Research Workflow</title>
  <style>
    body {{ max-width: 900px; margin: 2rem auto; padding: 0 1rem;
            font-family: -apple-system, sans-serif; line-height: 1.6; }}
    textarea {{ width: 100%; min-height: 7rem; padding: .75rem; }}
    button {{ margin-top: .75rem; padding: .65rem 1.2rem; }}
    pre {{ white-space: pre-wrap; background: #f5f5f5; padding: 1rem;
           border-radius: .5rem; }}
  </style>
</head>
<body>
  <h1>Math Research Workflow</h1>
  <p>PDF文献検索または安全制限付き多項式微分を選択します。</p>
  <form method="post">
    <textarea name="question" maxlength="2000">{html.escape(question)}</textarea>
    <br><button type="submit">質問する</button>
  </form>
  <h2>結果</h2>
  <pre>{html.escape(content)}</pre>
</body>
</html>"""


def format_result(result):
    lines = [f"選択された処理: {result['tool']}"]
    tool_result = result["tool_result"]

    if result["tool"] == "search_math_pdf":
        lines.append(f"検索用英語: {tool_result['search_question']}")
        lines.append(f"最高類似度: {tool_result['top_similarity']}")
        if tool_result["evidence"]:
            lines.append("検索根拠:")
        for item in tool_result["evidence"]:
            preview = " ".join(item["text"].split())[:160]
            lines.append(
                f"- PDF p. {item['pdf_page']} / "
                f"類似度 {item['similarity']:.4f}\n  {preview}…"
            )

    lines.append(f"\n回答:\n{result['answer']}")
    return "\n".join(lines)


class WorkflowHandler(BaseHTTPRequestHandler):
    def send_html(self, page, status=200):
        body = page.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        self.send_html(render_page())

    def do_POST(self):
        if self.path != "/":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self.send_html(render_page("入力サイズが不正です。"), status=400)
            return

        form = parse_qs(
            self.rfile.read(length).decode("utf-8", errors="replace")
        )
        question = form.get("question", [""])[0].strip()

        try:
            result = run_workflow(question)
            message = format_result(result)
            status = 200
        except WorkflowError as error:
            message = f"処理できません: {error}"
            status = 400
        except Exception:
            message = "予期しないエラーが発生しました。"
            status = 500

        self.send_html(render_page(message, question), status=status)

    def log_message(self, format_string, *args):
        print(f"UI: {format_string % args}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), WorkflowHandler)
    print(f"Open http://127.0.0.1:{args.port} in your browser.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nUIを終了します。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
