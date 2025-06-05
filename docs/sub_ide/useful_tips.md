
# VS code

## General

cntrl + shift + P : Open command palette

## Debug

ctrl + shift + F5 : Restart debugger
<https://www.geeksforgeeks.org/debug-keyboard-shortcuts-for-visual-studio-code/>

**Errors** :

encountered below error while opening preview of a file :

```
Error loading webview: Error: Could not register service workers: TypeError: Failed to register a ServiceWorker for scope
```

Solution:

In Windows, you can simply fix this error by clearing the cache for VSCode. Please follow the steps below:

- Close VSCode and also kill any background processes running in the task manager. Task Manager screenshot

- Go to the file explorer and to the path C:\Users\<user_name>\AppData\Roaming\Code and clear the contents of the folders Cache, CachedData, CachedExtensions, CachedExtensionVSIXs (if this folder exists) and Code Cache.

- Open VSCode and you are good to go.