# Version: 0.1.0 | 2026-11-02
import json
from pathlib import Path

import pytest
from cradle.engine.errors import ContentError
from cradle.platform.contentload import check_main, lint_strings, load_all


def write(root, path, rows, **header):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({'registry': target.stem, 'schema_version': 1,
                                  'rows': rows, **header}))
    return target


def test_loader_order_and_immutability(tmp_path):
    # Spec §5.0 / ADR-3: synthetic registries test the loader, never game state.
    paths = ['presentation/symbols.json', 'text/strings.json', 'world/scripts/site01.json',
             'world/sites/site01.json', 'registries/items.json']
    for path in paths:
        write(tmp_path, path, [{'id': 1, 'nested': [1, 2]}])
    regs = load_all(tmp_path)
    assert list(regs.files) == list(reversed(paths))
    assert len(regs.presentation) == 1
    with pytest.raises(TypeError):
        regs['registries/items.json']['rows'][0]['nested'][0] = 5
    with pytest.raises(TypeError):
        regs.files['new'] = {}


@pytest.mark.parametrize('header,rows', [({'schema_version': 2}, []),
    ({'schema_version': True}, []), ({'registry': ''}, []), ({}, 'bad'),
    ({}, [3]), ({}, [{'id': 1}, {'id': 1}]), ({}, [{'id': []}])])
def test_bad_registry_identifies_offender(tmp_path, header, rows):
    # Spec §11 / WP-1.5: file and row are observable.
    write(tmp_path, 'registries/bad.json', rows, **header)
    with pytest.raises(ContentError, match='registries/bad.json: row'):
        load_all(tmp_path)


def test_invalid_json_and_empty_pack(tmp_path):
    # WP-1.5: an empty pack must not report a successful content gate.
    assert check_main([str(tmp_path)]) == 1
    file = tmp_path / 'text' / 'bad.json'
    file.parent.mkdir()
    file.write_bytes(b'\xff')
    with pytest.raises(ContentError, match='invalid UTF-8 JSON'):
        load_all(tmp_path)


@pytest.mark.parametrize('word', ['magic', 'SPELL', 'god', 'divine', 'undead', 'zombie'])
def test_lint_rejects_forbidden_lexeme(tmp_path, word):
    # C-8 / spec §5.0: case-insensitive whole words.
    write(tmp_path, 'text/dialogue.json', [{'id': 1, 'text': f'A {word} appears.'}])
    with pytest.raises(ContentError, match='forbidden lexeme'):
        lint_strings(load_all(tmp_path))


def test_lint_preserved_scope_and_word_boundaries(tmp_path):
    # C-8: exception is scoped to the preserved row, never the whole file.
    write(tmp_path, 'text/dialogue.json', [{'id': 1, 'text': 'magic', 'preserved': True},
        {'id': 2, 'text': 'golden spelling divinewood'}])
    lint_strings(load_all(tmp_path))
    write(tmp_path, 'text/dialogue.json', [{'id': 1, 'text': 'magic', 'preserved': True},
        {'id': 2, 'text': 'magic'}])
    with pytest.raises(ContentError, match=r'rows\[1\]'):
        lint_strings(load_all(tmp_path))


def test_check_cli_success_and_failure(tmp_path, capsys):
    # WP-1.5: machine-visible exit status and named diagnostics.
    write(tmp_path, 'registries/synthetic.json', [{'id': 1}])
    assert check_main([str(tmp_path)]) == 0
    assert '1 registry' in capsys.readouterr().out
    write(tmp_path, 'text/dialogue.json', [{'text': 'spell'}])
    assert check_main([str(tmp_path)]) == 1
    assert 'text/dialogue.json' in capsys.readouterr().err


def test_fixture_blocklist_is_loadable():
    # WP-0.2 / C-8: exact supplied lexemes, missing C-9 list tracked in README.
    words = {line.strip() for line in (Path(__file__).parent / 'fixtures/lint_blocklist.txt').read_text().splitlines()
             if line.strip() and not line.startswith('#')}
    assert words == {'magic', 'spell', 'god', 'divine', 'undead', 'zombie'}
