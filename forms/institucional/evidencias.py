"""Anexos de evidência (foto/PDF) do Institucional: usa a mesma rotina da Visita Técnica
(redução de foto, validação, envio ao Drive/Apps Script), mas grava SEMPRE na pasta própria deste formulário."""
from forms.enfermagem.evidencias import (EvidenciaErro, UploadAppsScript, guardar_evidencia,  # noqa: F401
                                          nome_seguro, preparar_arquivo)
