set mainLabel to "com.andyzyj.y2a-auto"
set whisperLabel to "com.andyzyj.y2a-whisper"
set currentUserID to (do shell script "/usr/bin/id -u")
set guiDomain to "gui/" & currentUserID

set mainLoaded to my serviceIsLoaded(guiDomain, mainLabel)
set whisperLoaded to my serviceIsLoaded(guiDomain, whisperLabel)

if mainLoaded and whisperLoaded then
	set statusText to "Y2A 与本地 Whisper 当前正在运行。"
else if mainLoaded or whisperLoaded then
	set statusText to "Y2A 当前仅部分运行，启动可自动补齐服务。"
else
	set statusText to "Y2A 当前已停止。"
end if

set chosenButton to button returned of (display dialog statusText buttons {"取消", "停止运行", "启动并打开"} default button "启动并打开" with title "Y2A 控制")

if chosenButton is "停止运行" then
	my stopService(guiDomain, whisperLabel)
	my stopService(guiDomain, mainLabel)
	display notification "Y2A 与本地 Whisper 已停止，配置、模型和任务数据仍会保留。" with title "Y2A 控制"
else if chosenButton is "启动并打开" then
	try
		my startService(guiDomain, currentUserID, whisperLabel)
		my startService(guiDomain, currentUserID, mainLabel)
	on error errorMessage
		display alert "启动失败" message errorMessage as critical
		return
	end try

	set mainReady to my waitForURL("http://127.0.0.1:5051/", 30)
	set whisperReady to my waitForURL("http://127.0.0.1:5052/health", 30)
	if not mainReady then
		display alert "Y2A 启动超时" message "主平台未在预期时间内响应，请查看 Y2A 日志。" as critical
		return
	end if
	if not whisperReady then
		display alert "Whisper 启动超时" message "本地语音识别服务未在预期时间内响应，请查看 Whisper 日志。" as critical
		return
	end if

	open location "http://127.0.0.1:5051/"
	display notification "Y2A 与 large-v3-turbo 已启动并打开。" with title "Y2A 控制"
end if

on serviceIsLoaded(guiDomain, serviceLabel)
	try
		do shell script "/bin/launchctl print " & quoted form of (guiDomain & "/" & serviceLabel) & " >/dev/null 2>&1"
		return true
	on error
		return false
	end try
end serviceIsLoaded

on startService(guiDomain, currentUserID, serviceLabel)
	set serviceTarget to guiDomain & "/" & serviceLabel
	set plistPath to POSIX path of (path to home folder) & "Library/LaunchAgents/" & serviceLabel & ".plist"
	if not my serviceIsLoaded(guiDomain, serviceLabel) then
		try
			do shell script "/bin/launchctl bootstrap gui/" & currentUserID & " " & quoted form of plistPath
		on error errorMessage
			if errorMessage does not contain "service already loaded" and errorMessage does not contain "Input/output error" then error errorMessage
		end try
	end if
	do shell script "/bin/launchctl kickstart -k " & quoted form of serviceTarget
end startService

on stopService(guiDomain, serviceLabel)
	if my serviceIsLoaded(guiDomain, serviceLabel) then
		try
			do shell script "/bin/launchctl bootout " & quoted form of (guiDomain & "/" & serviceLabel)
		end try
	end if
end stopService

on waitForURL(targetURL, attempts)
	repeat with attemptNumber from 1 to attempts
		try
			do shell script "/usr/bin/curl --silent --fail --max-time 1 " & quoted form of targetURL & " >/dev/null"
			return true
		end try
		delay 0.5
	end repeat
	return false
end waitForURL
