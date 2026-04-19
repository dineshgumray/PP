import http.cookiejar
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "instance" / "ollama_profile_runs.jsonl"
WIZARD_LOG_PATH = ROOT / "instance" / "ollama_profile_wizard.log"
SERVER_LOG_PATH = ROOT / "instance" / "ollama_profile_server.log"


OLLAMA_PROFILE_CASES = [
    {
        "name": "product-leadership-update",
        "profile": {
            "name": "Aarav Sharma",
            "email": "aarav.ollama1@example.com",
            "password": "super-secret",
            "occupation": "Product Manager",
            "location": "Bengaluru, India",
            "date_of_birth": "1996-08-11",
            "goals": "Move into product leadership roles and write sharper executive updates.",
        },
        "payload": {
            "task": "Draft a quarterly product update for the leadership team.",
            "use_case": "business",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Leadership team",
            "desired_format": "Executive summary",
            "output_length": "Medium",
            "thinking_styles": "Strategic, concise",
        },
    },
    {
        "name": "linkedin-content-post",
        "profile": {
            "name": "Maya Johnson",
            "email": "maya.ollama2@example.com",
            "password": "super-secret",
            "occupation": "Content Strategist",
            "location": "Lagos, Nigeria",
            "date_of_birth": "1992-03-24",
            "goals": "Grow my LinkedIn audience with clear, consistent posts.",
        },
        "payload": {
            "task": "Write a LinkedIn post announcing a career pivot.",
            "use_case": "content",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "LinkedIn followers",
            "desired_format": "Social post",
            "output_length": "Short",
            "thinking_styles": "Creative, engaging",
        },
    },
    {
        "name": "python-api-debugging",
        "profile": {
            "name": "Luis Martinez",
            "email": "luis.ollama3@example.com",
            "password": "super-secret",
            "occupation": "Backend Engineer",
            "location": "Austin, USA",
            "date_of_birth": "1990-12-02",
            "goals": "Debug Python APIs faster and ship cleaner services.",
        },
        "payload": {
            "task": "Explain how to implement cursor pagination in a Python API.",
            "use_case": "coding",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Junior developers",
            "desired_format": "Technical explanation",
            "output_length": "Medium",
            "thinking_styles": "Precise, implementation-focused",
        },
    },
    {
        "name": "study-guide",
        "profile": {
            "name": "Priya Nair",
            "email": "priya.ollama4@example.com",
            "password": "super-secret",
            "occupation": "Graduate Student",
            "location": "Toronto, Canada",
            "date_of_birth": "1998-05-17",
            "goals": "Pass the machine learning exam and make better study notes.",
        },
        "payload": {
            "task": "Create a study sheet on gradient descent and overfitting.",
            "use_case": "study",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Self-study",
            "desired_format": "Study guide",
            "output_length": "Medium",
            "thinking_styles": "Clear, patient",
        },
    },
    {
        "name": "travel-itinerary",
        "profile": {
            "name": "Sofia Rossi",
            "email": "sofia.ollama5@example.com",
            "password": "super-secret",
            "occupation": "Travel Planner",
            "location": "Madrid, Spain",
            "date_of_birth": "1989-09-08",
            "goals": "Plan travel itineraries and practical trip logistics.",
        },
        "payload": {
            "task": "Build a 3-day Tokyo itinerary with transit tips.",
            "use_case": "travel",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Solo traveler",
            "desired_format": "Itinerary",
            "output_length": "Medium",
            "thinking_styles": "Practical, cost-aware",
        },
    },
    {
        "name": "investor-update",
        "profile": {
            "name": "Noah Kim",
            "email": "noah.ollama6@example.com",
            "password": "super-secret",
            "occupation": "Startup Founder",
            "location": "Singapore",
            "date_of_birth": "1991-01-30",
            "goals": "Write concise investor updates and explain revenue trends better.",
        },
        "payload": {
            "task": "Summarize monthly revenue, churn, and next steps for investors.",
            "use_case": "business",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Investors",
            "desired_format": "Investor update",
            "output_length": "Short",
            "thinking_styles": "Decision-oriented, concise",
        },
    },
    {
        "name": "research-brief",
        "profile": {
            "name": "Elena Petrova",
            "email": "elena.ollama7@example.com",
            "password": "super-secret",
            "occupation": "Research Analyst",
            "location": "Boston, USA",
            "date_of_birth": "1994-07-19",
            "goals": "Synthesize evidence from studies and present careful findings.",
        },
        "payload": {
            "task": "Summarize the latest findings on remote work productivity.",
            "use_case": "research",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Policy team",
            "desired_format": "Research brief",
            "output_length": "Medium",
            "thinking_styles": "Evidence-aware, structured",
        },
    },
    {
        "name": "brand-bio",
        "profile": {
            "name": "Jordan Lee",
            "email": "jordan.ollama8@example.com",
            "password": "super-secret",
            "occupation": "Brand Consultant",
            "location": "Cape Town, South Africa",
            "date_of_birth": "1993-11-04",
            "goals": "Strengthen my LinkedIn brand and portfolio voice.",
        },
        "payload": {
            "task": "Rewrite my bio for a portfolio site.",
            "use_case": "personal-brand",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Hiring managers",
            "desired_format": "Bio",
            "output_length": "Short",
            "thinking_styles": "Authentic, polished",
        },
    },
    {
        "name": "general-checklist",
        "profile": {
            "name": "Hannah Brooks",
            "email": "hannah.ollama9@example.com",
            "password": "super-secret",
            "occupation": "Operations Manager",
            "location": "Chicago, USA",
            "date_of_birth": "1988-02-15",
            "goals": "Need direct practical answers for onboarding checklists and daily planning.",
        },
        "payload": {
            "task": "Create a simple onboarding checklist for a new hire.",
            "use_case": "general",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "New teammate",
            "desired_format": "Checklist",
            "output_length": "Short",
            "thinking_styles": "Structured, direct",
        },
    },
    {
        "name": "career-outreach-email",
        "profile": {
            "name": "Imani Clarke",
            "email": "imani.ollama10@example.com",
            "password": "super-secret",
            "occupation": "Marketing Lead",
            "location": "London, UK",
            "date_of_birth": "1991-06-09",
            "goals": "Move into head of marketing roles and write stronger outreach emails.",
        },
        "payload": {
            "task": "Draft a cold outreach email for a product design partnership.",
            "use_case": "career",
            "target_provider": "ollama",
            "mode": "generate",
            "audience": "Design director",
            "desired_format": "Email draft",
            "output_length": "Short",
            "thinking_styles": "Confident, persuasive",
        },
    },
]


def pick_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(base_url, timeout_seconds=90):
    deadline = time.time() + timeout_seconds
    last_error = None

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/", timeout=2) as response:
                response.read()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)

    raise RuntimeError(f"Server did not become ready: {last_error}")


def build_opener():
    cookie_jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))


def post_form(opener, url, form_data):
    payload = urllib.parse.urlencode(form_data).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    with opener.open(request, timeout=30) as response:
        response.read()
        return response.getcode()


def post_json(opener, url, payload):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json")

    try:
        with opener.open(request, timeout=300) as response:
            raw = response.read().decode("utf-8")
            status_code = response.getcode()
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status_code = exc.code

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"raw": raw}

    return status_code, parsed, raw


def append_report(entry):
    with REPORT_PATH.open("a", encoding="utf-8") as report_file:
        report_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_case(opener, base_url, case):
    started = time.perf_counter()
    signup_status = None
    error = None
    response_status = None
    response_payload = {}
    raw_response = ""

    try:
        signup_status = post_form(opener, f"{base_url}/signup", case["profile"])
        response_status, response_payload, raw_response = post_json(
            opener,
            f"{base_url}/api/generate",
            case["payload"],
        )
    except Exception as exc:
        error = str(exc)

    elapsed_seconds = round(time.perf_counter() - started, 3)
    report_entry = {
        "case": case["name"],
        "profile": {
            "name": case["profile"]["name"],
            "email": case["profile"]["email"],
            "occupation": case["profile"]["occupation"],
            "location": case["profile"]["location"],
        },
        "task": case["payload"]["task"],
        "signup_status": signup_status,
        "http_status": response_status,
        "status": response_payload.get("status"),
        "provider": response_payload.get("provider"),
        "mode": response_payload.get("mode"),
        "model": response_payload.get("model"),
        "response_text": response_payload.get("response_text"),
        "handoff_note": response_payload.get("handoff_note"),
        "optimized_prompt_excerpt": response_payload.get("optimized_prompt", "")[:500],
        "raw_response_excerpt": raw_response[:500],
        "duration_seconds": elapsed_seconds,
        "error": error,
    }
    append_report(report_entry)
    return report_entry


def main():
    instance_dir = ROOT / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("", encoding="utf-8")
    WIZARD_LOG_PATH.write_text("", encoding="utf-8")
    SERVER_LOG_PATH.write_text("", encoding="utf-8")

    run_db_fd, run_db_path = tempfile.mkstemp(prefix="ollama_profile_", suffix=".db", dir=str(instance_dir))
    os.close(run_db_fd)

    port = pick_free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(
        {
            "PORT": str(port),
            "DATABASE": run_db_path,
            "LOG_FILE": str(WIZARD_LOG_PATH),
            "OLLAMA_URL": env.get("OLLAMA_URL", "http://127.0.0.1:11434"),
            "OLLAMA_MODEL": env.get("OLLAMA_MODEL", "llama3.2:3b"),
            "LLM_TIMEOUT": env.get("LLM_TIMEOUT", "300"),
        }
    )

    server_log = SERVER_LOG_PATH.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, str(ROOT / "app.py")],
        cwd=str(ROOT),
        env=env,
        stdout=server_log,
        stderr=subprocess.STDOUT,
    )

    try:
        wait_for_server(base_url)
        opener = build_opener()
        results = []

        print(f"Running live Ollama scenarios against {base_url}")
        for case in OLLAMA_PROFILE_CASES:
            report_entry = run_case(opener, base_url, case)
            results.append(report_entry)
            print(
                f"{case['name']}: "
                f"{report_entry['status']} "
                f"(HTTP {report_entry['http_status']}, {report_entry['duration_seconds']}s)"
            )

        generated_count = sum(1 for entry in results if entry.get("status") == "generated")
        print(f"Completed {len(results)} cases; {generated_count} generated successfully.")
        print(f"JSONL report: {REPORT_PATH}")
        print(f"Wizard log: {WIZARD_LOG_PATH}")
        print(f"Server log: {SERVER_LOG_PATH}")

        if generated_count != len(results):
            return 1
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=15)

        server_log.close()
        try:
            Path(run_db_path).unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
