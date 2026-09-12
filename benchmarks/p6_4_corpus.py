"""Inert, newly generated CC0-1.0 fixtures for the accepted P6.4 comparison."""

from cybersecgpt.tokenizer import (
    EvaluationDomain,
    EvaluationManifest,
    EvaluationSample,
)

SOURCE_REF = "generated:cybersecgpt-tokenizer:p6.4"
LICENSE_ID = "CC0-1.0"


def _sample(sample_id: str, domain: EvaluationDomain, text: str) -> EvaluationSample:
    return EvaluationSample.from_text(
        sample_id=sample_id,
        domain=domain,
        text=text,
        source_ref=SOURCE_REF,
        license_id=LICENSE_ID,
    )


CONSTRUCTION_MANIFEST = EvaluationManifest(
    manifest_id="p6.4-generated-construction",
    version="1",
    samples=(
        _sample(
            "train-natural-language-en-kha-001",
            EvaluationDomain.NATURAL_LANGUAGE,
            (
                "The defensive analyst reviews evidence before recording a finding. "
                "U nongpeit jingshngain u bishar ïa ki sakhi shuwa ban thoh ïa ka rai. "
            )
            * 8,
        ),
        _sample(
            "train-code-python-c-001",
            EvaluationDomain.CODE,
            (
                "def verify(record):\n    return record.status == 'supported'\n"
                "int verify(int status) { return status == 1; }\n"
            )
            * 8,
        ),
        _sample(
            "train-code-assembly-shell-001",
            EvaluationDomain.CODE,
            (
                "mov eax, status\ncmp eax, 1\njne reject\n"
                "$status = 'review'; Write-Output $status\n"
                "status=review; printf '%s\\n' \"$status\"\n"
            )
            * 8,
        ),
        _sample(
            "train-logs-windows-linux-001",
            EvaluationDomain.LOGS,
            (
                "2026-01-01T00:00:00Z host=lab-win event=login result=allowed\n"
                "2026-01-01T00:00:01Z host=lab-linux service=sshd result=denied\n"
            )
            * 8,
        ),
        _sample(
            "train-structured-json-yaml-xml-001",
            EvaluationDomain.STRUCTURED_DATA,
            (
                '{"asset":"lab","state":"observed","count":2}\n'
                "asset: lab\nstate: observed\ncount: 2\n"
                '<asset state="observed">lab</asset>\n'
            )
            * 8,
        ),
        _sample(
            "train-network-http-dns-001",
            EvaluationDomain.NETWORK,
            (
                "GET /health HTTP/1.1\r\nHost: lab.example.invalid\r\n\r\n"
                "query=telemetry.lab.example.invalid type=AAAA action=observe\n"
            )
            * 8,
        ),
        _sample(
            "train-identifiers-001",
            EvaluationDomain.SECURITY_IDENTIFIERS,
            (
                "url=https://lab.example.invalid/report ip=192.0.2.25 "
                "ipv6=2001:db8::25 cve=CVE-2099-0001 "
                f"sha256={'0' * 64}\n"
            )
            * 8,
        ),
        _sample(
            "train-rules-sigma-yara-siem-001",
            EvaluationDomain.DETECTION_RULES,
            (
                "title: Generated Review Rule\ndetection:\n  condition: selection\n"
                "rule generated_review { condition: false }\n"
                "WHEN source='lab' THEN action='review'\n"
            )
            * 8,
        ),
        _sample(
            "train-rules-firewall-ids-iac-001",
            EvaluationDomain.DETECTION_RULES,
            (
                "deny tcp 192.0.2.0/24 any -> 198.51.100.0/24 9\n"
                "alert tcp any any -> 203.0.113.8 443 (msg:'generated'; sid:1;)\n"
                'resource "example_monitor" "lab" { enabled = true }\n'
            )
            * 8,
        ),
        _sample(
            "train-security-prose-001",
            EvaluationDomain.SECURITY_PROSE,
            (
                "The inert sample describes triage, containment, evidence quality, "
                "and threat-intelligence confidence without executable instructions. "
            )
            * 8,
        ),
    ),
)


EVALUATION_MANIFEST = EvaluationManifest(
    manifest_id="p6.4-generated-evaluation",
    version="1",
    samples=(
        _sample(
            "eval-natural-language-english-001",
            EvaluationDomain.NATURAL_LANGUAGE,
            "A verifier must preserve uncertainty when the available evidence "
            "is incomplete.",
        ),
        _sample(
            "eval-natural-language-khasi-001",
            EvaluationDomain.NATURAL_LANGUAGE,
            "Ka jingbishar kaba shngain ka dei ban pynneh ïa ka jingshisha "
            "bad ki sakhi.",
        ),
        _sample(
            "eval-code-python-001",
            EvaluationDomain.CODE,
            "def admit(scope: str) -> bool:\n    return scope == 'approved'\n",
        ),
        _sample(
            "eval-code-c-assembly-001",
            EvaluationDomain.CODE,
            "int bounded(int n) { return n >= 0 && n <= 512; }\n"
            "mov eax, 512\ncmp ebx, eax\n",
        ),
        _sample(
            "eval-code-powershell-shell-001",
            EvaluationDomain.CODE,
            "$state = 'cancelled'; Write-Output $state\n"
            "state=cancelled; printf '%s\\n' \"$state\"\n",
        ),
        _sample(
            "eval-logs-windows-001",
            EvaluationDomain.LOGS,
            "2026-02-03T04:05:06Z host=lab-win event_id=4624 "
            "account=sample result=success",
        ),
        _sample(
            "eval-logs-linux-001",
            EvaluationDomain.LOGS,
            "Feb 03 04:05:07 lab-linux sshd[1200]: generated authentication failure",
        ),
        _sample(
            "eval-structured-json-yaml-001",
            EvaluationDomain.STRUCTURED_DATA,
            '{"finding":{"status":"unsupported","confidence":0}}\n'
            "status: review\ncount: 3\n",
        ),
        _sample(
            "eval-structured-xml-telemetry-001",
            EvaluationDomain.STRUCTURED_DATA,
            '<telemetry source="lab"><metric name="queue">4</metric></telemetry>',
        ),
        _sample(
            "eval-network-http-001",
            EvaluationDomain.NETWORK,
            "POST /events HTTP/1.1\r\nHost: sensor.example.invalid\r\n"
            "Content-Length: 0\r\n\r\n",
        ),
        _sample(
            "eval-network-dns-001",
            EvaluationDomain.NETWORK,
            "query=updates.sensor.example.invalid type=A answer=198.51.100.40 ttl=300",
        ),
        _sample(
            "eval-identifiers-url-ip-hash-cve-001",
            EvaluationDomain.SECURITY_IDENTIFIERS,
            "https://example.invalid/advisory 203.0.113.19 2001:db8:1::19 "
            f"{'a1' * 32} CVE-2099-12345",
        ),
        _sample(
            "eval-rules-sigma-yara-001",
            EvaluationDomain.DETECTION_RULES,
            "title: Inert Generated Rule\ndetection:\n  selection:\n"
            "    EventID: 1\n  condition: selection\n"
            "rule inert_generated { condition: false }",
        ),
        _sample(
            "eval-rules-siem-firewall-ids-001",
            EvaluationDomain.DETECTION_RULES,
            "SIEM WHERE severity='review'; deny udp 192.0.2.0/24 any -> any 9; "
            "alert tcp any any -> 198.51.100.9 443 (msg:'observe'; sid:2;)",
        ),
        _sample(
            "eval-rules-iac-001",
            EvaluationDomain.DETECTION_RULES,
            'resource "generated_sensor" "example" { network_mode = "offline" '
            "enabled = true }",
        ),
        _sample(
            "eval-security-prose-malware-analysis-001",
            EvaluationDomain.SECURITY_PROSE,
            "Defensive static analysis recorded an inert marker and requested "
            "human review; no sample was executed.",
        ),
        _sample(
            "eval-security-prose-threat-intel-001",
            EvaluationDomain.SECURITY_PROSE,
            "The generated intelligence note separates observation, inference, "
            "confidence, and unresolved contradiction.",
        ),
    ),
)
