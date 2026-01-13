import os
from openai import OpenAI
import json
import time
import re

class DisasterAgent:
    def __init__(self, model_id="deepseek/deepseek-v3.2", api_token=None, max_tokens=500, tools=None):
        """
        Initialize the HuggingFace Chatbot using the OpenAI client.
        
        Args:
            model_id (str): The HuggingFace model ID to use. 
                            Defaults to 'deepseek/deepseek-v3.2'.
            api_token (str): Optional HuggingFace API token.
            max_tokens (int): Maximum tokens for the response. Defaults to 500.
            tools (dict): Optional dictionary of tool functions. 
                          Format: {"tool_name": function_reference}
        """
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.tools = tools or {}
        
        # Use provided token or fall back to environment variable
        token = api_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
        
        if not token:
            # We can't initialize the client properly without a token for this endpoint
            self.client = None
        else:
            self.client = OpenAI(
                base_url="https://api.novita.ai/openai",
                api_key=token,
            )

    # before calling model, run tools locally if needed
    def _prefetch_tools(self, user_input):
        low = user_input.lower()
        results = {}
        # Explicit trigger to decrease latency
        #if "news" in low or "flood" in low or "latest" in low:
        try:
            results["google_news"] = self.tools.get("get_google_news", lambda **_: "No tool")(query=user_input)
        except Exception as e:
            results["google_news"] = f"Error: {e}"
        #try:
            #make results entry for nws_alerts if lat/lon found
        #except Exception as e:
            #results["google_news"] = f"Error: {e}"
        # add other tool triggers as needed
        return results

    def _normalize_dsml_text(self, s: str) -> str:
        """Normalize DSML-like text: convert fullwidth bars to ascii, unescape common HTML entities,
        remove zero-width characters, and normalize quotes so regexes match more reliably."""
        if not s:
            return s
        # replace fullwidth vertical bar with ASCII bar
        s = s.replace('\uFF5C', '|').replace('｜', '|')
        # unescape common HTML entities that models sometimes emit
        s = s.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        # normalize smart quotes to plain quotes
        s = s.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
        # remove zero-width and BOM characters
        s = re.sub(r'[\u200B-\u200D\uFEFF]', '', s)
        return s

    def get_response(self, user_input, history=None):
        """
        Generate a response from the chatbot.
        
        Args:
            user_input (str): The user's message.
            history (list): List of previous messages (optional, for context).
                            Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        
        Returns:
            str: The chatbot's response.
        """
        start = time.time()
        if not self.client:
            return "Error: API Token is missing. Please provide a HuggingFace API Token."

        # Construct messages list
        messages = []
        
        # System prompt
        #"You are a helpful assistant that helps identify areas of most need during natural disaster events. "
        #"You are an expert in disaster coordination, volunteering, and donation logistics. "
        #"IMPORTANT: This model does NOT have direct internet access. Any external data you may use is provided below by the application. "
        #"Use only the supplied tool outputs and the conversation history to answer queries about current events or local conditions. "
        #"If the provided data does not contain the requested information, clearly state that the information is unavailable rather than guessing or inventing facts. "
        #"Prioritize concise, structured, and verifiable guidance for disaster coordination."
        system_prompt = (
            "You are a helpful assistant that helps identify areas of most need during natural disaster events. "
            "You are an expert in disaster coordination, volunteering, and donation logistics. "
            "IMPORTANT: Always search for data using the provided tools (Google News, NWS Alerts, OpenFEMA) "
            "before making claims about specific community needs or disaster status. "
            "If you want to call a tool, return exactly a single JSON object with keys tool and args "
            "(args must be valid JSON). Do not wrap in other text. "
            "If you do not have data from a tool for a specific inquiry about a location's needs, "
            "clearly state that you don't have that information instead of speculating or fabricating needs. "
            "Keep answers concise, structured, and helpful."
        )
        """
            "You are a helpful assistant that helps identify areas of most need during natural disaster events. "
            "You are an expert in disaster coordination, volunteering, and donation logistics. "
            "IMPORTANT: This model does NOT have direct internet access — any external data must come from the application. "
            "When you need external data, request it as structured tool calls rather than embedding facts you don't have. "
            "Preferred formats, in order: "
            "If the platform supports function-calling, use the function-calling API. "
            "Otherwise, emit one or more DSML <｜DSML｜invoke ...> blocks (one per call). "
            "If neither is available, return a JSON array named tool_calls where each item is {\"tool\":\"<tool_name>\",\"args\":{...}}. "
            "When asking for tool calls, output only the structured tool-call representation (no extra commentary). "
            "After tools return results, synthesize a concise, verifiable answer in English using only the provided data and conversation history. "
            "If the requested information is not present in the supplied data, explicitly say it is unavailable."
            "Keep responses concise, structured, and helpful."
        """
        messages.append({"role": "system", "content": system_prompt})
        
        # History
        if history:
            # Ensure history format matches OpenAI expectations (role/content)
            messages.extend(history)
        
        # Current user input
        messages.append({"role": "user", "content": user_input})
        
        # Define tools schema
        tools_schema = [
            {
                "type": "function",
                "function": {
                    "name": "get_google_news",
                    "description": "Get recent flash flood news for a specific location or search query.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query or location to search for news (e.g., 'Nashville flood')."
                            }
                        },
                        "required": ["query"] 
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_nws_alerts",
                    "description": "Get active weather alerts from the National Weather Service for a specific latitude and longitude.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lat": {
                                "type": "number",
                                "description": "Latitude of the location."
                            },
                            "lon": {
                                "type": "number",
                                "description": "Longitude of the location."
                            }
                        },
                        "required": ["lat", "lon"] 
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_fema_disaster_declarations",
                    "description": "Get recent FEMA disaster declarations for a specific state and optionally a county.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string",
                                "description": "The two-letter state abbreviation (e.g., 'TN')."
                            },
                            "county": {
                                "type": "string",
                                "description": "The county name (e.g., 'Davidson')."
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to look back (default is 365)."
                            }
                        },
                        "required": ["state"] 
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_fema_assistance_data",
                    "description": "Get summary data for FEMA Individual Assistance approved in a state/county to gauge community need.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "state": {
                                "type": "string",
                                "description": "The two-letter state abbreviation (e.g., 'TN')."
                            },
                            "county": {
                                "type": "string",
                                "description": "The county name (e.g., 'Davidson')."
                            }
                        },
                        "required": ["state"] 
                    }
                }
            }
        ]
        
        try:
            """tool_outputs = self._prefetch_tools(user_input)
            print(f"Prefetched tool outputs: {tool_outputs}")
            if tool_outputs:
                # Summarize / shorten outputs for processing
                summary_parts = []
                for name, out in tool_outputs.items():
                    txt = str(out)
                    if len(txt) > 2000:
                        txt = txt[:2000] + " ...[truncated]"
                    summary_parts.append(f"=== {name} ===\n{txt}")
                messages.append({"role": "system", "content": "Tool outputs (fetched by the app):\n" + "\n\n".join(summary_parts)})"""
    
            # Iterative tool-call processing loop. Some models will request
            # multiple tool calls in sequence; keep processing until the model
            # returns a final response or we hit a safety iteration limit.
            max_iterations = 6
            iteration = 0
            while True:
                # Sanitize outgoing messages: convert any 'tool' messages without a truthy
                # 'tool_call_id' into assistant-fallbacks to avoid router ordering errors.
                try:
                    for i, m in enumerate(list(messages)):
                        if isinstance(m, dict) and m.get("role") == "tool":
                            if not m.get("tool_call_id"):
                                print(f"[DisasterAgent] Converting malformed tool message at index {i} to assistant fallback:", m.get("name"))
                                messages[i] = {"role": "assistant", "content": f"[tool:{m.get('name')}]\n{m.get('content')}"}
                except Exception:
                    pass

                # Validate message ordering and tool-call linkage before sending.
                try:
                    problems = []
                    for i, m in enumerate(messages):
                        if isinstance(m, dict) and m.get("role") == "tool":
                            if i == 0:
                                problems.append((i, "tool message at start of conversation"))
                                continue
                            prev = messages[i-1]
                            if not isinstance(prev, dict) or prev.get("role") != "assistant":
                                problems.append((i, f"tool message not immediately after assistant (prev role={getattr(prev,'get', lambda k:None)('role')})"))
                                continue
                            # Check that preceding assistant declared matching tool_calls id
                            tc_list = prev.get("tool_calls") or []
                            match = False
                            for tc in tc_list:
                                try:
                                    if tc.get("id") and tc.get("id") == m.get("tool_call_id"):
                                        match = True
                                        break
                                except Exception:
                                    continue
                            if not match:
                                problems.append((i, f"tool_call_id {m.get('tool_call_id')} not found in preceding assistant.tool_calls"))
                    if problems:
                        print("[DisasterAgent] Message validator found potential issues:")
                        for idx, msg in problems:
                            print(f" - index {idx}: {msg}")
                        print("[DisasterAgent] Attempting automatic fallback conversion for offending tool messages.")
                        for idx, _ in problems:
                            try:
                                m = messages[idx]
                                if isinstance(m, dict) and m.get('role') == 'tool' and not m.get('tool_call_id'):
                                    messages[idx] = {"role": "assistant", "content": f"[tool:{m.get('name')}]\n{m.get('content')}"}
                            except Exception:
                                pass
                except Exception:
                    pass

                # First/next API call
                print(f"\nAttempting iteration {iteration}\n\n{messages}")
                completion = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    tools=tools_schema,
                    tool_choice="auto",
                    max_tokens=self.max_tokens,
                )
                print(f"\nIteration {iteration}\n\n{completion}")

                response_message = completion.choices[0].message

                # If the SDK populated tool_calls, execute them
                if getattr(response_message, 'tool_calls', None):
                    # Build minimal tool_calls (only include entries with a truthy id)
                    tc_list = []
                    for tc in response_message.tool_calls:
                        try:
                            tcid = getattr(tc, 'id', None)
                            fname = tc.function.name
                            fargs = tc.function.arguments
                        except Exception:
                            tcid = None
                            fname = getattr(tc, 'name', None) or (getattr(tc, 'function', {}) or {}).get('name')
                            fargs = getattr(tc, 'arguments', None) or (getattr(tc, 'function', {}) or {}).get('arguments')
                        if tcid:
                            tc_list.append({"id": tcid, "type": "function", "function": {"name": fname, "arguments": fargs}})

                    assistant_msg = {"role": "assistant", "content": response_message.content or ""}
                    if tc_list:
                        assistant_msg["tool_calls"] = tc_list
                    messages.append(assistant_msg)

                    for tool_call in response_message.tool_calls:
                        function_name = getattr(tool_call.function, 'name', None) if getattr(tool_call, 'function', None) else getattr(tool_call, 'name', None)
                        raw_args = getattr(tool_call.function, 'arguments', None) if getattr(tool_call, 'function', None) else getattr(tool_call, 'arguments', None)
                        try:
                            function_args = self._safe_json_loads(raw_args)
                        except Exception as json_err:
                            print(f"Error parsing tool arguments for {function_name}: {json_err}")
                            print(f"Raw arguments: {raw_args}")
                            tcid = getattr(tool_call, 'id', None)
                            if tcid:
                                messages.append({
                                    "role": "tool",
                                    "name": function_name,
                                    "content": f"Error: Invalid JSON arguments returned by model for tool '{function_name}'.",
                                    "tool_call_id": tcid,
                                })
                            else:
                                messages.append({
                                    "role": "assistant",
                                    "content": f"[tool:{function_name}]\nError: Invalid JSON arguments returned by model for tool '{function_name}'.",
                                })
                            continue

                        # Coerce common types
                        for k, v in list(function_args.items()):
                            if isinstance(v, str):
                                sv = v.strip()
                                if sv.lstrip('-').replace('.', '', 1).isdigit():
                                    try:
                                        function_args[k] = float(sv) if '.' in sv else int(sv)
                                    except Exception:
                                        pass
                        if 'state' in function_args:
                            try:
                                function_args['state'] = str(function_args['state']).upper()
                            except Exception:
                                pass

                        if function_name in self.tools:
                            tool_func = self.tools[function_name]
                            try:
                                tool_result = tool_func(**function_args)
                            except TypeError:
                                try:
                                    tool_result = tool_func(*function_args.values())
                                except Exception as tool_err:
                                    tool_result = f"Error executing tool: {str(tool_err)}"
                            except Exception as tool_err:
                                tool_result = f"Error executing tool: {str(tool_err)}"
                        else:
                            tool_result = f"Error: Tool '{function_name}' not found."

                        tcid = getattr(tool_call, 'id', None)
                        if tcid:
                            messages.append({
                                "role": "tool",
                                "name": function_name,
                                "content": str(tool_result),
                                "tool_call_id": tcid,
                            })
                        else:
                            messages.append({
                                "role": "assistant",
                                "content": f"[tool:{function_name}]\n{str(tool_result)}",
                            })

                    iteration += 1
                    if iteration >= max_iterations:
                        return "Error: Reached maximum tool-call iterations."
                    # continue loop to call model again with tool outputs
                    continue

                # If no SDK tool_calls, check for DSML-style invokes in the content
                content = (response_message.content or "")
                normalized = self._normalize_dsml_text(content)
                invoke_re = re.compile(
                    r"<\s*[｜|]?\s*DSML\s*[｜|]?\s*invoke\b[^>]*name=[\"']([^\"']+)[\"'][^>]*>(.*?)</\s*[｜|]?\s*DSML\s*[｜|]?\s*invoke\s*>",
                    re.S | re.I,
                )
                param_re = re.compile(
                    r"<\s*[｜|]?\s*DSML\s*[｜|]?\s*parameter\b[^>]*name=[\"']([^\"']+)[\"'][^>]*>(.*?)</\s*[｜|]?\s*DSML\s*[｜|]?\s*parameter\s*>",
                    re.S | re.I,
                )
                dsml_calls = []
                for im in invoke_re.finditer(normalized):
                    func_name = im.group(1)
                    body = im.group(2)
                    args = {}
                    for pm in param_re.finditer(body):
                        k = pm.group(1)
                        v = pm.group(2).strip()
                        args[k] = v
                    dsml_calls.append({"name": func_name, "arguments": args})

                if dsml_calls:
                    messages.append({"role": "assistant", "content": content})
                    for call in dsml_calls:
                        function_name = call.get("name")
                        raw_args = call.get("arguments", {})
                        # Coerce numeric args
                        coerced_args = {}
                        for k, v in raw_args.items():
                            if isinstance(v, str):
                                sv = v.strip()
                                if sv.lstrip('-').replace('.', '', 1).isdigit():
                                    try:
                                        coerced_args[k] = float(sv) if '.' in sv else int(sv)
                                        continue
                                    except Exception:
                                        pass
                                coerced_args[k] = sv
                            else:
                                coerced_args[k] = v

                        if function_name in self.tools:
                            try:
                                tool_func = self.tools[function_name]
                                try:
                                    tool_result = tool_func(**coerced_args)
                                except TypeError:
                                    tool_result = tool_func(*coerced_args.values())
                            except Exception as tool_err:
                                tool_result = f"Error executing tool: {str(tool_err)}"
                        else:
                            tool_result = f"Error: Tool '{function_name}' not found."

                        messages.append({
                            "role": "tool",
                            "name": function_name,
                            "content": str(tool_result),
                        })

                    iteration += 1
                    if iteration >= max_iterations:
                        return "Error: Reached maximum tool-call iterations."
                    continue

                # No tool calls detected; return final content
                return f"{self._clean_response(response_message.content)}\n\n*(Response generated in {time.time() - start:.2f} seconds; used {iteration} consecutive tool call/s)*"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Error connecting to chatbot: {str(e)}"

    def _safe_json_loads(self, s):
        """
        Attempt to parse JSON while handling potential extra data from reasoning models.
        """
        if not s:
            return {}
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            # Common issue with reasoning models: JSON followed by <think> or other text
            import re
            # Extract anything between the first { and the last }
            match = re.search(r'(\{.*\})', s, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            raise

    def _clean_response(self, content):
        """
        Remove <think>...</think> tags and clean up the response.
        """
        if not content:
            return ""
        import re
        # Remove reasoning blocks
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        return content.strip()

if __name__ == "__main__":
    # Test with tools
    from app.chatbot.tools.google_news import get_google_news
    from app.chatbot.tools.nws_alerts import get_nws_alerts
    
    test_tools = {
        "get_google_news": get_google_news,
        "get_nws_alerts": get_nws_alerts
    }
    
    bot = DisasterAgent(tools=test_tools)
    print(bot.get_response("Are there any weather alerts for Nashville (36.16, -86.78)?"))
    print(bot.get_response("What is the latest news on floods in Tennessee?"))