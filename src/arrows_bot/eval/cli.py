import os

import click

from arrows_bot.eval import annotate, collect, evaluate, report


@click.group()
def cli():
    pass


@cli.command("collect")
@click.option("--out", required=True, help="Directory to save screenshots")
@click.option("--count", default=10, show_default=True, help="Number of screenshots to capture")
@click.option("--prefix", default="shot", show_default=True, help="Filename prefix")
def collect_cmd(out, count, prefix):
    collect.collect_screenshots(out, count, prefix)


@cli.command("collect-level")
@click.option("--level-id", required=True, help="Level identifier, e.g. level_001")
@click.option(
    "--difficulty",
    required=True,
    type=click.Choice(["easy", "hard", "super_hard"]),
    help="Level difficulty (independent of viewport count)",
)
@click.option("--count", default=1, show_default=True, help="Number of viewports to capture")
@click.option("--notes", default=None, help="Optional notes about this level")
@click.option("--session", default=None, help="Optional collection session id")
@click.option("--pause", default=3.0, show_default=True, help="Seconds to wait between viewports")
def collect_level_cmd(level_id, difficulty, count, notes, session, pause):
    collect.collect_level(level_id, difficulty, count, notes, session, pause)


@cli.command("validate-level")
@click.option("--level-id", required=True, help="Level identifier to validate")
def validate_level_cmd(level_id):
    meta_path = os.path.join("data", "raw", level_id, "metadata.json")
    meta = collect.load_metadata(meta_path)
    if meta is None:
        raise click.ClickException(f"no metadata.json found for level {level_id!r}")
    collect.validate_metadata(meta)
    print(f"[validate-level] {level_id}: difficulty={meta['difficulty']} "
          f"viewport_count={meta['viewport_count']} viewports={[v['file'] for v in meta['viewports']]}")
    print("[validate-level] metadata OK")


@cli.command("annotate")
@click.option("--image", required=True, help="Path to screenshot to annotate")
@click.option(
    "--out",
    default=None,
    help="Output JSON path (default: data/annotations/<scenario>/<name>.json)",
)
@click.option(
    "--terminal",
    is_flag=True,
    default=False,
    show_default=True,
    help="Use the terminal-based annotator instead of the GUI",
)
def annotate_cmd(image, out, terminal):
    if out is None:
        out = annotate.default_annotation_path(image)
    annotate.annotate_image(image, out, use_terminal=terminal)


@cli.command("evaluate")
@click.option("--data", required=True, help="Root dir of raw screenshots")
@click.option("--annotations", required=True, help="Root dir of annotation JSONs")
@click.option("--out", required=True, help="Results output dir")
@click.option("--dist", default=20.0, show_default=True, help="Matching distance threshold (px)")
def evaluate_cmd(data, annotations, out, dist):
    evaluate.run_evaluation(data, annotations, out, dist)


@cli.command("report")
@click.option("--results", required=True, help="Results dir containing results.json")
def report_cmd(results):
    report.generate_report(results)


if __name__ == "__main__":
    cli()
