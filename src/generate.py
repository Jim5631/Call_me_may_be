from typing import Any, Callable

from llm_sdk import Small_LLM_Model

from .pyndantic import Function

TokenRule = Callable[[str], bool | None]


def for_number(token: str) -> bool | None:
    if token.strip() in (",", "}"):
        return None
    for c in token:
        if not (c.isdigit() or c in "-."):
            return False
    return True


def for_string(token: str) -> bool | None:
    if token == '"':
        return None
    if "\u010a" in token:
        return None
    for c in token:
        if c == '"':
            return False
    return True


def generate_value(
    model: Small_LLM_Model,
    ids: list[int],
    id_tok: dict[int, str],
    function: TokenRule,
) -> tuple[str, list[int]]:
    text = ""
    for _ in range(30):
        log = model.get_logits_from_input_ids(ids)
        masked_logits = [float("-inf")] * len(log)
        for token_id, token_text in id_tok.items():
            stat = function(token_text)
            if stat is not False:
                masked_logits[token_id] = log[token_id]

        n_token = masked_logits.index(max(masked_logits))
        select_token = id_tok[n_token]
        stat_select = function(select_token)

        if stat_select is None:
            break
        else:
            clean = select_token.replace("\u0120", " ")
            text += clean
            ids.append(n_token)
    return text, ids


def parameter_for_function(
    model: Small_LLM_Model,
    ids: list[int],
    id_tok: dict[int, str],
    selected_func: str,
    v_func_def: list[Function],
    user_request: str,
) -> tuple[dict[str, Any], list[int]]:
    obj = next((f for f in v_func_def if f.name == selected_func))
    parameters: dict[str, Any] = {}
    reminder = f"\nQuestion: {user_request}\nArguments as JSON: "
    ids = ids + model.encode(reminder)[0].tolist()
    ids = ids + model.encode('{"')[0].tolist()
    for i, (name, paramater) in enumerate(list(obj.parameters.items())):
        ids = ids + model.encode(f'"{name}":')[0].tolist()
        if paramater.type == "number":
            text, ids = generate_value(model, ids, id_tok, for_number)
            parameters[name] = float(text)
        else:
            ids = ids + model.encode('"')[0].tolist()
            text, ids = generate_value(model, ids, id_tok, for_string)
            ids = ids + model.encode('"')[0].tolist()
            parameters[name] = text
            if i < len(list(obj.parameters.items())) - 1:
                ids = ids + model.encode(', "')[0].tolist()
    return parameters, ids
