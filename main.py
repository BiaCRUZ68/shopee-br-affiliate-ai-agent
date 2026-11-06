
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.discovery import discover
from src.campaigns import campaign_for

ROOT = Path(__file__).resolve().parent


def format_report(data, campaigns):
    lines = [
        "# Shopee Brasil — Radar de Oportunidades",
        "",
        f"Gerado em: {data['generated_at']}",
        "",
        "## Classificação de nichos",
        "",
        "Scores indicam prioridade de pesquisa, não vendas Shopee.",
        "",
        "| Nicho | Score | Trends | Notícias | Evidência |",
        "|---|---:|---:|---:|---|",
    ]

    for item in data["results"]:
        lines.append(
            f"| {item['niche']} | {item['score']:.1f} "
            f"| {item['trending_matches']} "
            f"| {item['news_matches']} "
            f"| {item['confidence']} |"
        )

    lines += ["", "## Campanhas VideoExpress.ai", ""]

    for campaign in campaigns:
        lines += [
            f"### {campaign['project_title']}",
            "",
            f"**Título:** {campaign['viral_youtube_title']}",
            "",
            f"**Descrição:** {campaign['youtube_description']}",
            "",
            f"**Ângulo:** {campaign['video_angle']}",
            "",
            "**Thumbnail Text-to-Image:**",
            campaign["thumbnail_text_to_image_prompt"],
            "",
        ]

        for scene in campaign["scenes"]:
            lines += [
                f"#### Cena {scene['number']} — 8 segundos",
                "",
                "**Text-to-Image:**",
                scene["text_to_image_prompt"],
                "",
                "**Image-to-Video:**",
                scene["image_to_video_prompt"],
                "",
                "**Text-to-Voiceover:**",
                scene["text_to_voiceover_prompt"],
                "",
            ]

    if data["warnings"]:
        lines += ["## Avisos de coleta", ""]
        lines += [f"- {w}" for w in data["warnings"]]

    return "\n".join(lines)


def main():
    config = json.loads(
        (ROOT / "config/settings.json").read_text(
            encoding="utf-8"
        )
    )

    data = discover(config)

    eligible = [
        item for item in data["results"]
        if item["has_live_evidence"]
        and item["news_matches"] >= config.get(
            "min_news_for_campaign", 1
        )
    ]

    selected = eligible[:config.get("top_niches", 5)]
    campaigns = [campaign_for(item) for item in selected]

    data["campaigns"] = campaigns
    data["status"] = (
        "evidence_found" if campaigns
        else "no_qualified_opportunities"
    )

    report_dir = ROOT / "reports"
    report_dir.mkdir(exist_ok=True)

    date = datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).strftime("%Y-%m-%d")

    json_content = json.dumps(
        data, ensure_ascii=False, indent=2
    )
    markdown = format_report(data, campaigns)

    (report_dir / "latest.json").write_text(
        json_content, encoding="utf-8"
    )
    (report_dir / "latest.md").write_text(
        markdown, encoding="utf-8"
    )

    (report_dir / f"{date}.json").write_text(
        json_content, encoding="utf-8"
    )
    (report_dir / f"{date}.md").write_text(
        markdown, encoding="utf-8"
    )

    print(f"Niches researched: {len(data['results'])}")
    print(f"Campaigns generated: {len(campaigns)}")
    print(f"Status: {data['status']}")
    print(f"Report: reports/{date}.md")


if __name__ == "__main__":
    main()
