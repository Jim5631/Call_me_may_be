"""Entry point: turn natural language prompts into function calls."""
import argparse
import json
import os
import sys

try:
    from llm_sdk import Small_LLM_Model
except BaseException:
    sys.exit(1)
from .contraint import constrain_function_selection
from .generate import parameter_for_function
from .pyndantic import Function, InputModel, OutputModel, load
from .validate import validate_l


def parse() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Function calling")
    parser.add_argument(
        "--functions_definition",
        type=str,
        default="data/input/functions_definition.json",
        help="Path to function definition",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/input/function_calling_tests.json",
        help="Path to test prompts",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/output/function_calling_results.json",
        help="Path to the result",
    )
    return parser.parse_args()


def load_vocab(model: Small_LLM_Model) -> dict[int, str]:
    """Load the vocabulary as a token id -> token text mapping."""
    vocab = load(model.get_path_to_vocab_file())
    return {int(token_id): text for text, token_id in vocab.items()}


def build_functions_block(v_func_def: list[Function]) -> str:
    """Describe the available functions, one per line."""
    return "\n".join(f"- {f.name}: {f.description}" for f in v_func_def)


def build_prompt(user_request: str, functions_block: str) -> str:
    """Build the prompt used for function selection."""
    return (
        f"Available functions:\n{functions_block}\n\n"
        f"User question: {user_request}\n"
        "Function to call:"
    )


def process_prompt(
    model: Small_LLM_Model,
    id_tok: dict[int, str],
    v_func_def: list[Function],
    functions_block: str,
    user_request: str,
) -> OutputModel:
    """Select a function and extract its parameters for one prompt."""
    names = [f.name for f in v_func_def]
    prompt = build_prompt(user_request, functions_block)
    selected_func, ids = constrain_function_selection(
        model, prompt, id_tok, names
    )
    parameters, ids = parameter_for_function(
        model, ids, id_tok, selected_func, v_func_def, user_request
    )
    return OutputModel(
        prompt=user_request, name=selected_func, parameters=parameters
    )


def write_results(results: list[OutputModel], output_path: str) -> None:
    """Write all results to the output JSON file."""
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in results], f, indent=2)


def run() -> None:
    """Run the whole pipeline."""
    args = parse()
    v_func_def = validate_l(load(args.functions_definition), Function)
    v_input = validate_l(load(args.input), InputModel)

    model = Small_LLM_Model()
    id_tok = load_vocab(model)
    functions_block = build_functions_block(v_func_def)

    results: list[OutputModel] = []
    for item in v_input:
        try:
            result = process_prompt(
                model, id_tok, v_func_def, functions_block, item.prompt
            )
        except ValueError as e:
            print(f"Skipping prompt {item.prompt!r}: {e}")
            continue
        print(f"prompt: {result.prompt}\n name: {result.name}\n"
              f" parameters: {result.parameters}\n")
        results.append(result)

    write_results(results, args.output)


def main() -> None:
    """Run the pipeline and report errors without crashing."""
    try:
        run()
    except FileNotFoundError as e:
        print(f"Error: file not found: {e.filename}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        print(e)
