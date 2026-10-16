Write-Host "SlideKick Presentation Integration Test"

Write-Host "NEXT SLIDE TEST"
Write-Host "Focus your slideshow. Command executes in 5 seconds."

Start-Sleep -Seconds 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/next" `
    -Method Post

Write-Host "Did the slideshow advance?"
Read-Host "Press Enter to continue"

Write-Host "PREVIOUS SLIDE TEST"
Write-Host "Focus your slideshow. Command executes in 5 seconds."

Start-Sleep -Seconds 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/previous" `
    -Method Post

Write-Host "Did the slideshow move backward?"