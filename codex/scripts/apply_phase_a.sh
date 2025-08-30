#!/usr/bin/env bash
set -euo pipefail
codex apply codex/cr/CR-BOOT.yaml
codex apply codex/cr/CR-A-01-temporal-slotconfig.yaml
codex apply codex/cr/CR-A-02-neuron-focus-fields.yaml
codex apply codex/cr/CR-A-03-slotengine-anchor-logic.yaml
codex apply codex/cr/CR-A-04-growth-neuron.yaml
codex apply codex/cr/CR-A-05-tests.yaml
