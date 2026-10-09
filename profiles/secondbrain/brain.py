"""Source-checkout development CLI. NOT a certified evidence preservation system."""
import argparse
import json
import os
import sys
from brain_core.verify import IntegrityFailure, verify_object
from brain_core.object import ObjectFailure, create_object, verify_object_link
from brain_core.capture import CaptureFailure, capture_file, verify_capture
from brain_core.writer import WriterFailure, configure_writer, publish_capture, verify_publication
from brain_core.custody import CustodyFailure, commit_capture, verify_commit, verify_chain, _canon
from brain_core.checkpoint import CheckpointFailure, create_checkpoint, verify_checkpoint


def main(argv=None):
    parser = argparse.ArgumentParser(prog='brain', description='Development only: Capture, local Vault, unanchored custody ledger (not certified)')
    commands = parser.add_subparsers(dest='group', required=True)
    objects = commands.add_parser('object', help='Content-addressed object operations')
    object_commands = objects.add_subparsers(dest='action', required=True)
    verify = object_commands.add_parser('verify', help='Compare local bytes with a v2 canonical object record')
    verify.add_argument('object_id')
    verify.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    verify.add_argument('--json', action='store_true')

    create_obj = object_commands.add_parser('create', help='Publish unsealed local metadata + per-capture custody linkage')
    create_obj.add_argument('capture_id')
    create_obj.add_argument('--device-id', required=True)
    create_obj.add_argument('--writer-id', required=True)
    create_obj.add_argument('--writer-epoch', default=os.environ.get('SECOND_BRAIN_WRITER_EPOCH'))
    create_obj.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    create_obj.add_argument('--json', action='store_true')
    verify_link = object_commands.add_parser('verify-link', help='Read-only Capture/Vault/Observation/Custody linkage check')
    verify_link.add_argument('capture_id')
    verify_link.add_argument('--device-id', required=True)
    verify_link.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    verify_link.add_argument('--json', action='store_true')

    captures = commands.add_parser('capture', help='Capture-only landing (NOT sealed evidence)')
    capture_commands = captures.add_subparsers(dest='action', required=True)
    capture = capture_commands.add_parser('file', help='Copy source into Inbox without deleting source')
    capture.add_argument('source')
    capture.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    capture.add_argument('--device-id', required=True)
    capture.add_argument('--collector', required=True)
    capture.add_argument('--capture-id')
    capture.add_argument('--json', action='store_true')
    check_capture = capture_commands.add_parser('verify', help='Verify Inbox capture and receipt')
    check_capture.add_argument('capture_id')
    check_capture.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    check_capture.add_argument('--device-id', required=True)
    check_capture.add_argument('--json', action='store_true')

    writers = commands.add_parser('writer', help='S1 local writer policy + UNCOMMITTED Vault publication')
    writer_commands = writers.add_subparsers(dest='action', required=True)
    init = writer_commands.add_parser('init', help='One-time local writer policy registration (not a distributed lock)')
    init.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    init.add_argument('--writer-id', required=True)
    init.add_argument('--json', action='store_true')
    promote = writer_commands.add_parser('publish', help='Copy verified capture into Vault; NO custody or commit claim')
    promote.add_argument('capture_id')
    promote.add_argument('--device-id', required=True)
    promote.add_argument('--writer-id', required=True)
    promote.add_argument('--writer-epoch', default=os.environ.get('SECOND_BRAIN_WRITER_EPOCH'), required=False)
    promote.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    promote.add_argument('--json', action='store_true')
    inspect = writer_commands.add_parser('verify', help='Read-only check of uncommitted local Vault publication')
    inspect.add_argument('capture_id')
    inspect.add_argument('--device-id', required=True)
    inspect.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    inspect.add_argument('--json', action='store_true')

    custody = commands.add_parser('custody', help='R9 local RFC8785 hash chain (NOT externally anchored)')
    custody_cmd = custody.add_subparsers(dest='action', required=True)
    commit = custody_cmd.add_parser('commit', help='Append Acquisition/Custody pair and local receipt')
    commit.add_argument('capture_id')
    commit.add_argument('--device-id', required=True)
    commit.add_argument('--writer-id', required=True)
    commit.add_argument('--writer-epoch', default=os.environ.get('SECOND_BRAIN_WRITER_EPOCH'))
    commit.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    commit.add_argument('--json', action='store_true')
    check = custody_cmd.add_parser('verify', help='Verify local receipt and complete event chain')
    check.add_argument('capture_id')
    check.add_argument('--device-id', required=True)
    check.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    check.add_argument('--json', action='store_true')
    ledger = custody_cmd.add_parser('chain', help='Read-only verify local event chain')
    ledger.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    ledger.add_argument('--json', action='store_true')

    checkpoints = commands.add_parser('checkpoint', help='R10 operator-managed external checkpoint (not notarization)')
    checkpoint_commands = checkpoints.add_subparsers(dest='action', required=True)
    export = checkpoint_commands.add_parser('export', help='Print checkpoint JSON; operator must store it outside root')
    export.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    export.add_argument('--json', action='store_true')
    check_anchor = checkpoint_commands.add_parser('verify', help='Compare chain with operator-supplied independent checkpoint')
    check_anchor.add_argument('checkpoint_path')
    check_anchor.add_argument('--root', default=os.environ.get('SECOND_BRAIN_ROOT'))
    check_anchor.add_argument('--json', action='store_true')

    args = parser.parse_args(argv)
    if not args.root:
        result, exit_code = {'status': 'FAIL', 'error_code': 'ROOT_NOT_SET'}, 2
    elif ((args.group in ('writer', 'custody') and args.action in ('publish', 'commit')) or
          (args.group == 'object' and args.action == 'create')) and not args.writer_epoch:
        result, exit_code = {'status': 'FAIL', 'error_code': 'WRITER_EPOCH_NOT_SET'}, 2
    else:
        try:
            if args.group == 'object':
                if args.action == 'verify':
                    result = verify_object(args.root, args.object_id)
                elif args.action == 'verify-link':
                    result = verify_object_link(args.root, args.device_id, args.capture_id)
                else:
                    result = create_object(args.root, args.device_id, args.capture_id, args.writer_id, args.writer_epoch)
            elif args.group == 'capture':
                if args.action == 'file':
                    result = capture_file(args.root, args.source, args.device_id, args.collector,
                                          capture_id=args.capture_id)
                else:
                    result = verify_capture(args.root, args.device_id, args.capture_id)
            elif args.group == 'checkpoint':
                result = (create_checkpoint(args.root) if args.action == 'export'
                          else verify_checkpoint(args.root, args.checkpoint_path))
            elif args.group == 'custody':
                if args.action == 'chain':
                    result = verify_chain(args.root)
                elif args.action == 'verify':
                    result = verify_commit(args.root, args.device_id, args.capture_id)
                else:
                    result = commit_capture(args.root, args.device_id, args.capture_id, args.writer_id, args.writer_epoch)
            elif args.action == 'init':
                result = configure_writer(args.root, args.writer_id)
            elif args.action == 'publish':
                result = publish_capture(args.root, args.device_id, args.capture_id, args.writer_id, args.writer_epoch)
            else:
                result = verify_publication(args.root, args.device_id, args.capture_id)
            exit_code = 0
        except (IntegrityFailure, CaptureFailure, WriterFailure, CustodyFailure, CheckpointFailure, ObjectFailure) as exc:
            result, exit_code = {'status': 'FAIL', 'error_code': exc.code}, 3
    if args.json:
        if args.group == 'checkpoint' and args.action == 'export' and exit_code == 0:
            print(_canon(result).decode('utf-8'))
        else:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif exit_code == 0:
        if args.group == 'object' and args.action == 'verify':
            print(f"PASS {result['object_id']} | sha256={result['sha256']} | bytes={result['size_bytes']}")
        elif args.group == 'object':
            print(f"{result['status']} {result['capture_id']} | object={result['object_id']}")
        elif args.group == 'capture':
            print(f"READY (uncommitted capture) {result['capture_id']} | sha256={result['sha256']}")
        elif args.action == 'init':
            print(f"WRITER CONFIGURED (policy only) epoch={result['writer_epoch']}")
        elif args.group == 'checkpoint':
            print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':')))
        elif args.group == 'custody' and args.action == 'chain':
            print(f"{result['status']} events={result['event_count']}")
        else:
            print(f"{result['status']} {result['capture_id']} | sha256={result['sha256']}")
    else:
        print('FAIL ' + result['error_code'], file=sys.stderr)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
