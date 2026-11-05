/**
 * Portal de Auditoria — recebe fotos/PDF e grava no Drive do dono do script.
 * Por que existe: uma conta de serviço não tem espaço de armazenamento próprio; num "Meu Drive" o Google recusa o envio
 * (storageQuotaExceeded). Este Web App roda COMO VOCÊ (dono das pastas) e grava com o seu espaço.
 *
 * Instalação (uma vez): script.google.com > Novo projeto > cole este código > Configurações do projeto >
 * Propriedades do script > adicione TOKEN = <uma senha longa qualquer> > Implantar > Nova implantação > App da Web:
 * "Executar como: Eu" e "Quem tem acesso: Qualquer pessoa" > copie a URL (termina em /exec).
 * No Streamlit (Settings > Secrets) acrescente:  [upload_drive]  url = "<URL /exec>"  token = "<o mesmo TOKEN>"
 */
function doPost(e) {
  try {
    var p = JSON.parse(e.postData.contents);
    var token = PropertiesService.getScriptProperties().getProperty('TOKEN');
    if (!token || p.token !== token) return _json({ok: false, erro: 'token inválido'});
    if (!p.pasta_pai) return _json({ok: false, erro: 'pasta_pai ausente'});
    var pai = DriveApp.getFolderById(p.pasta_pai);           // cada formulário envia a SUA pasta
    var it = pai.getFoldersByName(p.pasta);                   // subpasta = código da visita
    var sub = it.hasNext() ? it.next() : pai.createFolder(p.pasta);
    var blob = Utilities.newBlob(Utilities.base64Decode(p.dados_b64), p.mime, p.nome);
    var f = sub.createFile(blob);
    return _json({ok: true, id: f.getId(), link: f.getUrl()});
  } catch (err) {
    return _json({ok: false, erro: String(err)});
  }
}
function _json(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
