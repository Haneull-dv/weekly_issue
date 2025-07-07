"""
GPU 최적화 뉴스 요약 모델 예측기 
RTX 2080 + bitsandbytes 4bit 양자화 지원
"""
import os
import gc
import torch
import logging
from typing import Optional
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig
)
from peft import PeftModel

logger = logging.getLogger(__name__)

class SummarizerPredictor:
    """GPU 최적화 요약 모델 예측기 (RTX 2080 전용)"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        
        # GPU 강제 설정 (RTX 2080)
        if not torch.cuda.is_available():
            raise RuntimeError("❌ CUDA GPU가 필요합니다. RTX 2080이 감지되지 않았습니다.")
        
        self.device = "cuda:0"
        torch.cuda.set_device(0)  # RTX 2080 선택
        
        self.base_model_name = "skt/kogpt2-base-v2"  # KoGPT2 한국어 생성 모델
        
        # 학습된 LoRA 어댑터 경로 확인
        trained_adapter_path = "/app/slm_summarizer_training/outputs"
        if os.path.exists(trained_adapter_path) and os.path.exists(os.path.join(trained_adapter_path, "adapter_config.json")):
            self.model_path = trained_adapter_path
            logger.info(f"🎓 학습된 LoRA 어댑터 발견: {trained_adapter_path}")
        else:
            self.model_path = "./outputs"  # 폴백 경로
            logger.warning(f"⚠️ 학습된 어댑터 없음, 베이스 모델 사용")
        
        logger.info(f"🚀 GPU 환경 초기화 완료: {torch.cuda.get_device_name(0)}")
        logger.info(f"💾 GPU 메모리: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        
    async def load_model(self):
        """RTX 2080 GPU 최적화 모델 로딩"""
        try:
            logger.info("🔄 GPU 기반 KoGPT2 모델 로딩 시작...")
            
            # GPU 메모리 정리
            torch.cuda.empty_cache()
            gc.collect()
            
            # RTX 2080 최적화 4bit 양자화 설정
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_storage=torch.uint8,
                # RTX 2080 최적화
                llm_int8_threshold=6.0,
                llm_int8_has_fp16_weight=False
            )
            
            # KoGPT2 토크나이저 로딩 (오프라인 우선)
            logger.info("📖 KoGPT2 토크나이저 로딩...")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.base_model_name,
                    trust_remote_code=True,
                    use_fast=False,
                    local_files_only=False,  # HuggingFace Hub 허용
                    token=os.getenv("HUGGINGFACE_HUB_TOKEN")  # API 제한 우회
                )
                
                # KoGPT2 필수 설정
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                    self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
                
                self.tokenizer.padding_side = "left"
                self.tokenizer.model_max_length = 512
                
                logger.info(f"✅ 토크나이저 로딩 완료 (vocab: {self.tokenizer.vocab_size})")
                
            except Exception as e:
                logger.error(f"❌ 토크나이저 로딩 실패: {e}")
                raise
            
            # RTX 2080 최적화 베이스 모델 로딩 
            logger.info("🤖 KoGPT2 베이스 모델 로딩 (GPU + 4bit)...")
            try:
                base_model = AutoModelForCausalLM.from_pretrained(
                    self.base_model_name,
                    quantization_config=bnb_config,
                    device_map="auto",  # RTX 2080에 자동 배치
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                    low_cpu_mem_usage=True,
                    max_memory={0: "7GB"},  # RTX 2080 8GB 중 7GB 사용
                    use_cache=True,
                    attn_implementation="eager",  # RTX 2080 호환
                    token=os.getenv("HUGGINGFACE_HUB_TOKEN")
                )
                
                logger.info(f"✅ 베이스 모델 로딩 완료")
                
            except Exception as e:
                logger.error(f"❌ 베이스 모델 로딩 실패: {e}")
                # 폴백: 더 보수적인 설정
                logger.info("🔄 보수적 설정으로 재시도...")
                base_model = AutoModelForCausalLM.from_pretrained(
                    self.base_model_name,
                    quantization_config=bnb_config,
                    device_map={"": 0},  # 강제로 GPU 0에 배치
                    torch_dtype=torch.float16,
                    low_cpu_mem_usage=True,
                    token=os.getenv("HUGGINGFACE_HUB_TOKEN")
                )
            
            # LoRA 어댑터 확인 및 로딩
            if os.path.exists(self.model_path) and os.path.exists(os.path.join(self.model_path, "adapter_config.json")):
                logger.info(f"🔗 LoRA 어댑터 로딩: {self.model_path}")
                self.model = PeftModel.from_pretrained(base_model, self.model_path)
            else:
                logger.warning(f"⚠️ LoRA 어댑터 없음, 베이스 모델 사용: {self.model_path}")
                self.model = base_model
            
            # 추론 모드 설정
            self.model.eval()
            if hasattr(self.model, 'gradient_checkpointing_disable'):
                self.model.gradient_checkpointing_disable()
            
            # GPU 메모리 상태 확인
            memory_allocated = torch.cuda.memory_allocated(0) / 1e9
            memory_reserved = torch.cuda.memory_reserved(0) / 1e9
            logger.info(f"🎯 GPU 메모리 사용량: {memory_allocated:.2f}GB / {memory_reserved:.2f}GB")
            
            logger.info("🎉 GPU 최적화 KoGPT2 모델 로딩 완료!")
            
        except Exception as e:
            logger.error(f"💥 GPU 모델 로딩 실패: {str(e)}")
            raise e
    
    async def generate_summary(
        self,
        title: str,
        description: str,
        max_new_tokens: int = 100,  # RTX 2080 메모리 고려
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """GPU 최적화 요약 생성"""
        try:
            if self.model is None or self.tokenizer is None:
                raise ValueError("❌ 모델이 로드되지 않았습니다")
            
            # 프롬프트 구성
            prompt = self._create_prompt(title, description)
            
            # GPU 토크나이징
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=400,  # 입력 길이 제한 (RTX 2080 최적화)
                padding=True
            ).to(self.device)
            
            # GPU 추론
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                    no_repeat_ngram_size=3,
                    early_stopping=True,
                    use_cache=True
                )
            
            # 결과 디코딩
            generated_text = self.tokenizer.decode(
                outputs[0][inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            ).strip()
            
            # 정리
            summary = self._clean_generated_text(generated_text)
            
            # GPU 메모리 정리
            del inputs, outputs
            torch.cuda.empty_cache()
            
            return summary if summary else "요약을 생성할 수 없습니다."
            
        except Exception as e:
            logger.error(f"❌ GPU 요약 생성 실패: {str(e)}")
            torch.cuda.empty_cache()  # 에러 시에도 메모리 정리
            return f"요약 생성 중 오류 발생: {str(e)}"
    
    def _create_prompt(self, title: str, description: str) -> str:
        """KoGPT2 최적화 프롬프트 생성"""
        return f"""다음 뉴스를 한 문장으로 요약해주세요.

제목: {title}
내용: {description}

요약:"""

    def _clean_generated_text(self, text: str) -> str:
        """생성된 텍스트 정리"""
        if not text:
            return ""
        
        # 불필요한 문자 제거
        cleaned = text.split('\n')[0].strip()
        cleaned = cleaned.replace('요약:', '').strip()
        
        # 길이 제한 (너무 긴 요약 방지)
        if len(cleaned) > 200:
            cleaned = cleaned[:200] + "..."
        
        return cleaned
    
    def unload_model(self):
        """GPU 메모리에서 모델 언로드"""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer  
            self.tokenizer = None
        
        torch.cuda.empty_cache()
        gc.collect()
        logger.info("🗑️ GPU 모델 언로드 완료")
    
    def get_gpu_memory_info(self) -> dict:
        """GPU 메모리 정보 반환"""
        if torch.cuda.is_available():
            return {
                "allocated": torch.cuda.memory_allocated(0) / 1e9,
                "reserved": torch.cuda.memory_reserved(0) / 1e9,
                "total": torch.cuda.get_device_properties(0).total_memory / 1e9
            }
        return {}
    
    @property
    def is_loaded(self) -> bool:
        """모델 로드 상태 확인"""
        return self.model is not None and self.tokenizer is not None 