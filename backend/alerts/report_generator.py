from pathlib import Path
from datetime import datetime


def generate_incident_report(incident_data, output_file="incident_action_report.md"):
    """
    Generate an Incident Action Report in Markdown format.

    incident_data may contain:
    - victim_complaint
    - mule_hops
    - risk_scores
    - predicted_atm_cluster
    - patrol_action
    - lien_action
    """

    report_lines = [
        "# Incident Action Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 1. Victim Complaint",
        "",
        str(incident_data.get("victim_complaint", "Not provided")),
        "",
        "## 2. Mule-Hop Timeline",
        ""
    ]

    mule_hops = incident_data.get("mule_hops", [])

    if mule_hops:
        for hop in mule_hops:
            report_lines.append(f"- {hop}")
    else:
        report_lines.append("- No mule-hop information provided.")

    report_lines.extend([
        "",
        "## 3. AI Risk Scores",
        ""
    ])

    risk_scores = incident_data.get("risk_scores", {})

    if risk_scores:
        for name, score in risk_scores.items():
            report_lines.append(f"- **{name}:** {score}")
    else:
        report_lines.append("- No risk scores provided.")

    report_lines.extend([
        "",
        "## 4. Predicted Geographic ATM Cluster",
        "",
        str(
            incident_data.get(
                "predicted_atm_cluster",
                "Not provided"
            )
        ),
        "",
        "## 5. Actions Taken",
        ""
    ])

    actions = incident_data.get("actions_taken", [])

    if actions:
        for action in actions:
            report_lines.append(f"- {action}")
    else:
        report_lines.append("- No actions recorded.")

    report = "\n".join(report_lines)

    output_path = Path(output_file)
    output_path.write_text(report, encoding="utf-8")

    return str(output_path)


if __name__ == "__main__":
    sample_incident = {
        "victim_complaint": "Sample simulated complaint.",
        "mule_hops": [
            "Victim account -> Mule account A",
            "Mule account A -> Mule account B"
        ],
        "risk_scores": {
            "transaction_risk": 0.91,
            "cluster_risk": 0.87
        },
        "predicted_atm_cluster": (
            "28.6304, 77.2773 - Sample ATM cluster"
        ),
        "actions_taken": [
            "Patrol dispatched",
            "Simulated lien placed"
        ]
    }

    file_path = generate_incident_report(sample_incident)

    print(f"Report generated: {file_path}")