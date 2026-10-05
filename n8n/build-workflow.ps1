# Regenerates ai-news-digest.workflow.json from the files in code/.
# Run after editing any code/*.js:  powershell -File n8n\build-workflow.ps1
$dir = $PSScriptRoot
function Code($f) { [IO.File]::ReadAllText((Join-Path $dir "code\$f")) }
function Link($to) { @{ main = @(, @(@{ node = $to; type = "main"; index = 0 })) } }

$wf = [ordered]@{
  name  = "AI News Digest"
  nodes = @(
    [ordered]@{ id = "1"; name = "Every day 6:45 IST"; type = "n8n-nodes-base.scheduleTrigger"; typeVersion = 1.2; position = @(0, 0)
      parameters = @{ rule = @{ interval = @(@{ field = "cronExpression"; expression = "45 6 * * *" }) } } }
    [ordered]@{ id = "2"; name = "Feed List"; type = "n8n-nodes-base.code"; typeVersion = 2; position = @(220, 0)
      parameters = @{ jsCode = (Code "feeds.js") } }
    [ordered]@{ id = "3"; name = "Read RSS"; type = "n8n-nodes-base.rssFeedRead"; typeVersion = 1.1; position = @(440, 0)
      parameters = @{ url = '={{ $json.url }}'; options = @{} }; onError = "continueRegularOutput" }
    [ordered]@{ id = "4"; name = "Filter & Build Prompt"; type = "n8n-nodes-base.code"; typeVersion = 2; position = @(660, 0)
      parameters = @{ jsCode = (Code "build-request.js") } }
    [ordered]@{ id = "5"; name = "Claude"; type = "n8n-nodes-base.httpRequest"; typeVersion = 4.2; position = @(880, 0)
      parameters = [ordered]@{
        method = "POST"; url = "https://api.anthropic.com/v1/messages"
        authentication = "genericCredentialType"; genericAuthType = "httpHeaderAuth"
        sendHeaders = $true
        headerParameters = @{ parameters = @(
            @{ name = "anthropic-version"; value = "2023-06-01" }
            @{ name = "anthropic-beta"; value = "server-side-fallback-2026-07-01" }) }
        sendBody = $true; specifyBody = "json"; jsonBody = '={{ JSON.stringify($json.request) }}'
        options = @{ timeout = 300000 } } }
    [ordered]@{ id = "6"; name = "Format Telegram Message"; type = "n8n-nodes-base.code"; typeVersion = 2; position = @(1100, 0)
      parameters = @{ jsCode = (Code "format-message.js") } }
    [ordered]@{ id = "7"; name = "Send to Telegram"; type = "n8n-nodes-base.telegram"; typeVersion = 1.2; position = @(1320, 0)
      parameters = [ordered]@{ chatId = "YOUR_CHAT_ID"; text = '={{ $json.text }}'
        additionalFields = @{ parse_mode = "HTML"; disable_web_page_preview = $true; appendAttribution = $false } } }
  )
  connections = [ordered]@{
    "Every day 6:45 IST"      = Link "Feed List"
    "Feed List"               = Link "Read RSS"
    "Read RSS"                = Link "Filter & Build Prompt"
    "Filter & Build Prompt"   = Link "Claude"
    "Claude"                  = Link "Format Telegram Message"
    "Format Telegram Message" = Link "Send to Telegram"
  }
  settings = @{ executionOrder = "v1"; timezone = "Asia/Kolkata" }
}

$out = Join-Path $dir "ai-news-digest.workflow.json"
[IO.File]::WriteAllText($out, ($wf | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding $false))
$check = [IO.File]::ReadAllText($out) | ConvertFrom-Json
"wrote $out - nodes: $($check.nodes.Count), Feed List -> $($check.connections.'Feed List'.main[0][0].node)"
