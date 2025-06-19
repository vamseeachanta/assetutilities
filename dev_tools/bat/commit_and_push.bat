REM Recursively commit and push

REM https://stackoverflow.com/questions/4988226/how-do-i-pass-multiple-parameters-into-a-function-in-powershell

function foo($a, $b, $c) {
   "a: $a; b: $b; c: $c"
}

CALL foo 1 2 3


Function Test([string]$arg1, [string]$arg2)
{
    Write-Host "`$arg1 value: $arg1"
    Write-Host "`$arg2 value: $arg2"
}

Test("ABC", "DEF")

