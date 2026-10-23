"""Preserve the human bank when original one-shot campaign grants run late.

Initial resources and rescued-base resources are grants, even when stock CHK
uses SetTo. Native starting support, supply boxes and mining may precede them.
Computer resource actions retain SetTo, including shared-force initialization.
"""
import struct

from . import build_all_campaigns as maps


def _executors(chk, trigger, human):
    owners = chk.getsection('OWNR')
    selected = set()
    for selector, enabled in enumerate(trigger[2372:2400]):
        if enabled:
            selected.update(maps.players_for(chk, selector, human))
    return sorted(p for p in selected if p < 8 and owners[p] in (3, 5, 6))


def _targets(chk, action, executor, human):
    selector = struct.unpack_from('<I', action, 16)[0]
    return {executor} if selector == 13 else maps.players_for(chk, selector, human)


def _terminal_objective(mission, index, action_index, action):
    # The Kel-Morian Combine completes the mining objective after every enemy
    # Command Center is gone. This is a victory threshold, not a base grant.
    if (mission['mission_id'], index, action_index) != (603, 21, 0):
        return False
    assert struct.unpack_from('<IIHBB', action, 16) == (18, 10500, 0, 26, 7)
    return True


def audit(chk, mission):
    """Inventory every enabled human resource action, including force selectors."""
    result = []
    human = mission['owner']
    for ti, trigger in enumerate(maps.triggers(chk)):
        executors = _executors(chk, trigger, human)
        for ai, action in maps.actions(trigger):
            if action[26] != 26:
                continue
            contexts = [p for p in executors if human in _targets(chk, action, p, human)]
            if not contexts:
                continue
            amount = struct.unpack_from('<I', action, 20)[0]
            operation = action[27]
            terminal = _terminal_objective(mission, ti, ai, action)
            classification = ('terminal_objective' if terminal else
                              'one_shot_grant' if operation == 7 and amount else
                              'additive_grant' if operation == 8 else 'other')
            result.append(dict(trigger=ti, action=ai, selector=struct.unpack_from('<I', action, 16)[0],
                               amount=amount, resource=struct.unpack_from('<H', action, 24)[0],
                               operation=operation, executors=contexts, classification=classification,
                               waits_before=[i for i, a in maps.actions(trigger) if a[26] == 4 and i < ai],
                               conditions=[maps.cf(c) for _, c in maps.conditions(trigger)]))
    return result


def _action(action, target, operation):
    value = bytearray(action)
    struct.pack_into('<I', value, 16, target)
    value[27] = operation
    return bytes(value)


def apply(chk, mission):
    inventory = audit(chk, mission)
    grants = {(a['trigger'], a['action']): a for a in inventory if a['classification'] == 'one_shot_grant'}
    output = []
    splits = []
    human = mission['owner']
    for ti, trigger in enumerate(maps.triggers(chk)):
        selected = {ai: row for (index, ai), row in grants.items() if index == ti}
        if not selected:
            output.append(trigger)
            continue
        assert not any(a[26] == 3 for _, a in maps.actions(trigger)), ('Repeating resource reset needs review', mission['mission_id'], ti)
        executors = _executors(chk, trigger, human)
        # Cloning only a shared trigger preserves each executor's original
        # action order, waits, conditions and all non-resource actions.
        shared = len(executors) > 1
        if shared:
            splits.append(dict(source_trigger=ti, executors=executors, copies=len(executors)))
        for executor in (executors if shared else [executors[0]]):
            modified = bytearray(trigger)
            if shared:
                modified[2372:2400] = maps.owner_bytes(executor)
            # Retain disabled slots and stop markers as well as live actions.
            rebuilt = []
            for ai in range(64):
                action = trigger[320 + ai * 32:352 + ai * 32]
                if ai not in selected or human not in _targets(chk, action, executor, human):
                    rebuilt.append(action)
                    continue
                targets = _targets(chk, action, executor, human)
                contexts = selected[ai]['executors']
                credited_by = human if human in contexts else contexts[0]
                # A group SetTo may run once per force member. Add the human
                # grant once, while every original computer SetTo still runs.
                if targets == {human} and executor == credited_by:
                    rebuilt.append(_action(action, human, 8))
                else:
                    rebuilt.extend(_action(action, p, 7) for p in sorted(targets - {human}))
                    if executor == credited_by:
                        rebuilt.append(_action(action, human, 8))
            while rebuilt and rebuilt[-1] == bytes(32):
                rebuilt.pop()
            assert len(rebuilt) <= 64, ('Resource grant expansion exceeds CHK actions', mission['mission_id'], ti)
            modified[320:2368] = b''.join(rebuilt).ljust(2048, b'\0')
            output.append(bytes(modified))
    chk.setsection('TRIG', b''.join(output))
    return dict(revision=1, mission=mission['mission_id'], inventory=inventory,
                grants_preserving_balance=len(grants), shared_trigger_splits=splits,
                terminal_objectives_preserved=sum(a['classification'] == 'terminal_objective' for a in inventory),
                computer_resource_operations_preserved=True)
