import os
import json
import platformdirs
import torch
from typing import List, Union
from transformers import AutoModelForCausalLM, AutoTokenizer
from .base import EngineLM, CachedEngine

class ChatLocalLLM(EngineLM, CachedEngine):
    DEFAULT_SYSTEM_PROMPT = "You are a helpful, creative, and smart assistant."

    def __init__(
        self,
        model_string: str = "meta-llama/Meta-Llama-3-8B",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        **kwargs
    ):
        root = platformdirs.user_cache_dir("textgrad")
        cache_path = os.path.join(root, f"cache_transformers_{model_string.replace('/', '_')}.db")
        self.device = kwargs.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        super().__init__(cache_path=cache_path)

        self.system_prompt = system_prompt
        self.model_string = model_string

        self.tokenizer = AutoTokenizer.from_pretrained(model_string)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_string,
            torch_dtype=torch.float16,
            use_flash_attention_2=True,
            trust_remote_code=True
        )

        self.model.to(self.device)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"

    def _format_prompt(self, prompt: str, system_prompt: str = None) -> str:
        sys_prompt = system_prompt if system_prompt else self.system_prompt
        return f"System: {sys_prompt}\nHuman: {prompt}\n <|eot_id|>:"

    def generate(
        self,
        prompt: Union[str, List[str]],
        system_prompt: str = None,
        **kwargs
    ) -> str:
        if isinstance(prompt, list):
            prompt = "\n".join(prompt)
        return self._generate_response(prompt, system_prompt, **kwargs)

    def _generate_response(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
    ) -> str:
        cache_key = (system_prompt if system_prompt else self.system_prompt) + prompt
        
        if cache_hit := self._check_cache(cache_key):
            return cache_hit

        formatted_prompt = self._format_prompt(prompt, system_prompt)
        inputs = self.tokenizer(
            formatted_prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            add_special_tokens=True
        ).to(self.device)

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True if temperature > 0 else False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        # Decode with skip_special_tokens=False to preserve EOS tokens
        generated_tokens = output[0][inputs["input_ids"].shape[1]:]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=False)
        
        # Clean up response by splitting on EOS token or "Human:"
        # First try splitting on EOS token
        response_parts = response.split(self.tokenizer.eos_token)
        if len(response_parts) > 1:
            response_text = response_parts[0].strip()
        else:
            # Fallback to splitting on "Human:" if no EOS token found
            response_text = response.split("Human:")[0].strip()
        
        # Remove any remaining special tokens for the final output
        response_text = self.tokenizer.clean_up_tokenization(response_text)
        self._save_cache(cache_key, response_text)
        return response_text

    def __call__(self, prompt, **kwargs):
        return self.generate(prompt, **kwargs)