#!/bin/bash
# Atalho para o iniciar.ps1: sobe ou retoma a noite sem duplicar o que ja esta rodando.
cd "$(dirname "$0")/../.." || exit 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "orquestracao\\noite_0410\\iniciar.ps1"
