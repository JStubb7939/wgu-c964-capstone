# Version Update Report

## Summary
Successfully updated version placeholders in training and validation datasets.

### Training Set (training_set.jsonl)
- **Total lines processed**: 1,260
- **AVM examples (first 165 lines)**: 165
- **Versions updated**: 148 out of 150 res modules
- **Could not update**: 2 res modules (not in extracted_avm_data.jsonl)
  - Line 113: `avm/res/dev-center/devcenter`
  - Line 147: `avm/res/azure-stack-hci/cluster`

### Validation Set (validation_set.jsonl)
- **Total lines processed**: 312
- **AVM examples (first 42 lines)**: 42
- **Versions updated**: 1 res module (line 1: `avm/res/aad/domain-service:0.5.0`)
- **Could not update**: 41 modules
  - 40 pattern (ptn) modules - not available in extracted_avm_data.jsonl
  - Pattern modules include:
    - `avm/ptn/virtual-machine-images/azure-image-builder`
    - `avm/ptn/subscription/service-health-alerts`
    - `avm/ptn/security/security-center`
    - `avm/ptn/sa/build-your-own-copilot`
    - `avm/ptn/sa/content-processing`
    - And 35 more pattern modules

## Total Results
- **Successfully updated**: 149 module references
- **Unable to update**: 43 module references
  - 2 res modules not in source data
  - 41 ptn modules not in source data

## Notes
- The extracted_avm_data.jsonl file only contains "res" (resource) modules
- Pattern (ptn) modules are deployment patterns/accelerators and are not included in the grounding data
- The 2 res modules that couldn't be updated (`dev-center/devcenter` and `azure-stack-hci/cluster`) may need to be added to the grounding data or handled separately
