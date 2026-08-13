# MetaRadar Security Standards

## Controls & Compliance Rules

1. **Zero Secret Leaks**: No API keys, passwords, or credentials committed to source control.
2. **PII/PHI Scrubbing**: Mandatory pattern matching (`PIIPHIScrubber`) before persistence or external provider transmission.
3. **Grok Privacy Gate**: `validate_privacy_gate` strictly blocks non-PUBLIC classifications from external LLM endpoints.
4. **Environment Isolation**: Database and Redis credentials driven strictly via environment variables.
