try:
    import sys
    from llm_sdk import Small_LLM_Model
except BaseException:
    sys.exit(1)


def constrain_function_selection(
    model: Small_LLM_Model,
    prompt: str,
    id_tok: dict[int, str],
    functions: list[str],
) -> tuple[str, list[int]]:
    ids: list[int] = model.encode(prompt)[0].tolist()
    text_generated = ""
    candidates = list(functions)

    while len(candidates) > 1:
        log = model.get_logits_from_input_ids(ids)
        masked_logits = [float("-inf")] * len(log)

        for token_id, token_text in id_tok.items():
            candidate_text = text_generated + token_text
            if any(cand.startswith(candidate_text) for cand in candidates):
                if token_id < len(log):
                    masked_logits[token_id] = log[token_id]

        best_logit = max(masked_logits)
        if best_logit == float("-inf"):
            break
        n_token = masked_logits.index(best_logit)
        ids.append(n_token)
        text_generated += id_tok[n_token]
        candidates = [c for c in candidates if c.startswith(text_generated)]

    return (candidates[0] if candidates else ""), ids
