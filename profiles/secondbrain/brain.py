"""Development-only CLI: capture-only landing and read-only object byte verification."""
import argparse
import json
import os
import sys
from brain_core.verify import IntegrityFailure, verify_object
from brain_core.capture import CaptureFailure, capture_file, verify_capture


def main(argv=None):
    parser = argparse.ArgumentParser(prog="brain", description="Development prototype: uncommitted capture landing and read-only object verification")
    commands = parser.add_subparsers(dest="group", required=True)
    objects = commands.add_parser("object", help="Content-addressed object operations")
    object_commands = objects.add_subparsers(dest="action", required=True)
    verify = object_commands.add_parser("verify", help="Compare actual local bytes with v2 object record")
    verify.add_argument("object_id")
    verify.add_argument("--root", default=os.environ.get("SECOND_BRAIN_ROOT"))
    verify.add_argument("--json", action="store_true")
    captures = commands.add_parser("capture", help="Capture-only landing (NOT sealed evidence)")
    capture_commands = captures.add_subparsers(dest="action", required=True)
    capture = capture_commands.add_parser("file", help="Copy source to append-only Inbox capture, source never deleted")
    capture.add_argument("source")
    capture.add_argument("--root", default=os.environ.get("SECOND_BRAIN_ROOT"))
    capture.add_argument("--device-id", required=True)
    capture.add_argument("--collector", required=True)
    capture.add_argument("--capture-id")
    capture.add_argument("--json", action="store_true")
    verify_capture_cmd = capture_commands.add_parser("verify", help="Verify Inbox capture bytes and receipt")
    verify_capture_cmd.add_argument("capture_id")
    verify_capture_cmd.add_argument("--root", default=os.environ.get("SECOND_BRAIN_ROOT"))
    verify_capture_cmd.add_argument("--device-id", required=True)
    verify_capture_cmd.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.root:
        result, exit_code = {"status": "FAIL", "error_code": "ROOT_NOT_SET"}, 2
    else:
        try:
            if args.group == "object":
                result = verify_object(args.root, args.object_id)
            elif args.action == "file":
                result = capture_file(args.root, args.source, args.device_id, args.collector,
                                      capture_id=args.capture_id)
            else:
                result = verify_capture(args.root, args.device_id, args.capture_id)
            exit_code = 0
        except (IntegrityFailure, CaptureFailure) as exc:
            result, exit_code = {"status": "FAIL", "error_code": exc.code}, 3
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif exit_code == 0:
        if args.group == "object":
            print(f"PASS {result['object_id']} | sha256={result['sha256']} | bytes={result['size_bytes']}")
        else:
            print(f"READY (uncommitted) {result['capture_id']} | sha256={result['sha256']} | bytes={result['size_bytes']}")
    else:
        print("FAIL " + result["error_code"], file=sys.stderr)
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
