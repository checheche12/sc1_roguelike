#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <string>
#include <vector>

static std::wstring quote(const std::wstring& input) {
    std::wstring out=L"\""; size_t slashes=0;
    for(wchar_t c:input) {
        if(c==L'\\') {++slashes; continue;}
        if(c==L'\"') out.append(slashes*2+1,L'\\');
        else out.append(slashes,L'\\');
        slashes=0; out+=c;
    }
    out.append(slashes*2,L'\\'); out+=L'\"'; return out;
}
int WINAPI wWinMain(HINSTANCE,HINSTANCE,PWSTR,int) {
    std::vector<wchar_t> buffer(32768);
    DWORD length=GetModuleFileNameW(nullptr,buffer.data(),static_cast<DWORD>(buffer.size()));
    if(!length || length>=buffer.size()) return 2;
    std::wstring folder(buffer.data(),length);
    folder.resize(folder.find_last_of(L"\\/"));
    std::wstring python=folder+L"\\runtime\\pythonw.exe";
    // Tcl 8.6 path normalization can lose inaccessible ancestor names.
    // Extended absolute paths keep relocated/Unicode library paths intact.
    std::wstring extended=folder;
    if(extended.rfind(L"\\\\?\\",0)!=0) {
        if(extended.rfind(L"\\\\",0)==0) extended=L"\\\\?\\UNC\\"+extended.substr(2);
        else extended=L"\\\\?\\"+extended;
    }
    if(!SetEnvironmentVariableW(L"TCL_LIBRARY",(extended+L"\\runtime\\tcl\\tcl8.6").c_str()) ||
       !SetEnvironmentVariableW(L"TK_LIBRARY",(extended+L"\\runtime\\tcl\\tk8.6").c_str())) return 4;
    int count=0; LPWSTR* args=CommandLineToArgvW(GetCommandLineW(),&count);
    bool probe=count==2 && std::wstring(args[1])==L"--self-test";
    std::wstring command=quote(python)+L" -E -s -X utf8 -m ";
    if(probe) command+=L"sc1.portable_runtime";
    else {
        command+=L"sc1.manager";
        if(count==1) command+=L" ui";
        for(int i=1;i<count;++i) command+=L" "+quote(args[i]);
    }
    LocalFree(args);
    STARTUPINFOW startup{}; startup.cb=sizeof(startup);
    PROCESS_INFORMATION process{};
    if(!CreateProcessW(python.c_str(),command.data(),nullptr,nullptr,FALSE,0,nullptr,folder.c_str(),&startup,&process)) {
        MessageBoxW(nullptr,L"포함된 실행 환경을 시작하지 못했습니다. ZIP 전체를 압축 해제한 후 다시 실행해 주세요.",L"캠페인 관리자",MB_OK|MB_ICONERROR);
        return 3;
    }
    CloseHandle(process.hThread);
    WaitForSingleObject(process.hProcess,INFINITE);
    DWORD result=1; GetExitCodeProcess(process.hProcess,&result); CloseHandle(process.hProcess);
    if(result && !probe) MessageBoxW(nullptr,L"관리자를 시작하지 못했습니다. 배포본의 파일이 모두 있는지 확인해 주세요.",L"캠페인 관리자",MB_OK|MB_ICONERROR);
    return static_cast<int>(result);
}
