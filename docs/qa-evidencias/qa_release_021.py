"""Auditoría release 0.2.1; usar carpeta de ejecución nueva; no modifica la aplicación."""
import dataclasses
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

QA=Path(__file__).resolve().parent
ROOT=QA.parents[1]
TF=ROOT.parent
sys.path.insert(0,str(ROOT))
from proteinfunc_app.core.integrity import verify_bundle
from proteinfunc_app.core.validation import validate_text,read_input_file

def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def save(path,data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def tree(root): return {p.relative_to(root).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(root.rglob('*')) if p.is_file()}
def command(out,name,cmd,cwd,timeout=300,extra_env=None):
    env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',
        HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
    if extra_env: env.update(extra_env)
    started=dt.datetime.now().astimezone().isoformat(); tick=time.perf_counter()
    try:
        p=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
        (out/(name+'.stdout.log')).write_text(p.stdout,encoding='utf-8')
        (out/(name+'.stderr.log')).write_text(p.stderr,encoding='utf-8')
        result={'command':cmd,'start':started,'seconds':time.perf_counter()-tick,'exit_code':p.returncode}
    except subprocess.TimeoutExpired as exc:
        (out/(name+'.stdout.log')).write_bytes(exc.stdout or b'')
        (out/(name+'.stderr.log')).write_bytes(exc.stderr or b'')
        result={'command':cmd,'start':started,'seconds':time.perf_counter()-tick,'error':'timeout'}
    save(out/(name+'.json'),result)
    print(name,result,flush=True)
    return result

def prepare(out):
    out.mkdir(parents=True,exist_ok=False)
    archive=out/'HISTORICO'; archive.mkdir()
    for name in ['INFORME_QA.md','MATRIZ_PRUEBAS.md','TRAZABILIDAD.md','RESUMEN_ACADEMICO.md']:
        shutil.copy2(QA/name,archive/name)
    old={p.relative_to(QA/'EVIDENCIAS').as_posix():sha(p) for p in sorted((QA/'EVIDENCIAS').rglob('*')) if p.is_file() and out not in p.parents}
    save(out/'evidencias_previas_sha256.json',old)
    for version in ('0.2.0','0.2.1'):
        save(out/f'distribucion-{version}-sha256.json',tree(TF/f'ProteinFuncAI {version}'))
    reports={}
    for label,bundle in [('fuente',ROOT/'model'),('0.2.0',TF/'ProteinFuncAI 0.2.0/_internal/model'),('0.2.1',TF/'ProteinFuncAI 0.2.1/_internal/model')]:
        r=verify_bundle(bundle)
        reports[label]={'ok':r.ok,'fingerprint':r.fingerprint,'checks':[dataclasses.asdict(x) for x in r.checks],
             'files':[dataclasses.asdict(x)|{'matches':x.matches} for x in r.files],'all_files':tree(bundle)}
    save(out/'integridad-modelos.json',reports)
    previous=json.loads((QA/'EVIDENCIAS/hashes_distribucion.json').read_text(encoding='utf-8'))
    save(out/'comparacion-binarios-020-previos.json',{name:sha(TF/'ProteinFuncAI 0.2.0'/name)==value['sha256'] for name,value in previous.items()})
    # Sin GUI: --version termina antes de crear QApplication e History.
    profile=out/'perfil-version'; profile.mkdir()
    command(out,'gui-version',[str(TF/'ProteinFuncAI 0.2.1/ProteinFuncAI.exe'),'--version'],out,
            extra_env={'LOCALAPPDATA':str(profile),'APPDATA':str(profile)})
    validation={}
    for name in ['muestra.fasta','con_errores.fasta','pruebas/07_adn_en_vez_de_proteina.fasta','pruebas/03_casos_limite.fasta']:
        r=validate_text(read_input_file(ROOT/'examples'/name),512)
        validation[name]={'summary':r.summary(),'global_errors':r.global_errors,
            'records':[{'id':x.record_id,'status':x.status,'accepted':x.accepted,'length':x.length,'messages':x.messages} for x in r.records]}
    controls={name:validate_text(seq,512) for name,seq in {'poliglicina':'G'*50,'diversidad_baja':'ACDE'*15,'ambiguos':'X'*30+'MKTAYIAKQR','corta':'ACGTACGT'}.items()}
    save(out/'mensajes-validacion-fuente-021.json',{'examples':validation,'controls':{k:[dataclasses.asdict(x) for x in v.records] for k,v in controls.items()}})
    assert validation['pruebas/07_adn_en_vez_de_proteina.fasta']['summary']=='3 registros · 1 válido · 2 con error'
    assert all(x['status']=='error' and 'ADN/ARN' in x['messages'][0] for x in validation['pruebas/07_adn_en_vez_de_proteina.fasta']['records'][:2])
    assert 'ocupa el 100%' in controls['poliglicina'].records[0].messages[0]
    assert '4 aminoácidos distintos' in controls['diversidad_baja'].records[0].messages[0]
    assert controls['corta'].records[0].accepted
    for label,name in [('cli-muestra','muestra.fasta'),('cli-errores','con_errores.fasta'),
        ('cli-adn-arn','pruebas/07_adn_en_vez_de_proteina.fasta'),('cli-limites','pruebas/03_casos_limite.fasta')]:
        command(out,label,[str(TF/'ProteinFuncAI 0.2.1/proteinfunc-check.exe'),str(ROOT/'examples'/name)],out)
    command(out,'pytest-validacion-inicial',[sys.executable,'-m','pytest','tests/test_validation.py','-v','-k',
        'dna_and_rna or low_complexity or example_test_files','-p','no:cacheprovider','--basetemp',tempfile.mkdtemp(prefix='qa021-validation-'),
        '--junitxml',str(out/'pytest-validacion-inicial.xml')],ROOT)

def pytest_all(out):
    py=TF/'.qa-venv-021/Scripts/python.exe'
    command(out,'pip-freeze',[str(py),'-m','pip','freeze'],ROOT)
    command(out,'pip-check',[str(py),'-m','pip','check'],ROOT)
    command(out,'pytest-completo-021',[str(py),'-m','pytest','tests','-v','-p','no:cacheprovider',
        '--basetemp',tempfile.mkdtemp(prefix='qa021-suite-'),'--junitxml',str(out/'pytest-completo-021.xml')],ROOT,timeout=1800,
        extra_env={'QT_QPA_PLATFORM':'offscreen'})

if __name__=='__main__':
    stage=sys.argv[1]; out=Path(sys.argv[2]).resolve()
    if stage=='prepare': prepare(out)
    elif stage=='pytest': pytest_all(out)
