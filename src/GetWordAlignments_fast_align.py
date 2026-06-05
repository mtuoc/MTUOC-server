#!/usr/bin/env python

import os
import subprocess
import sys
import threading
#from sacremoses import MosesTokenizer
import platform
import stat
from pathlib import Path
import requests
import time

# Simplified, non-threadsafe version for force_align.py
# Use the version in realtime for development
class WordAligner:
    def __init__(self, fwd_params, fwd_err, rev_params, rev_err, src_lang, tgt_lang, heuristic='grow-diag-final-and', fa_dir='./'):
        '''
        Class to perform sentence alignment from python using Fast align.
        * Parameters:
            * fwd_params: Forward probabilities learned using the fast_align scripts.
            * rev_params: Backward probabilities learned using the fast_align scripts.
            * fwd_err: Forward error file from fast_align scripts.
            * rev_err: Forward error file  learned using fast_align scripts.
            * src_lang: Source language in ISO format (two characters). Necessary for sacremoses tokenizer.
            * tgt_lang: Target language in ISO format (two characters). Necessary for sacremoses tokenizer.
            * heuristic: Heuristic to us in fast_align. By default: grow-diag-final-and
            * fa_dir: Path to the fast_align build.

        '''
        build_root = os.path.abspath(fa_dir)
        if platform.system()=="Windows":
            url = 'https://github.com/mtuoc/MTUOC-server/releases/download/v202511/fast_align.exe'
            nom_fitxer = 'fast_align.exe'
            ruta_fitxer = Path(nom_fitxer)
            if not ruta_fitxer.exists():
                try:
                    resposta = requests.get(url, stream=True)
                    resposta.raise_for_status()
                    with open(ruta_fitxer, 'wb') as fitxer:
                        for chunk in resposta.iter_content(chunk_size=8192):
                            if chunk:
                                fitxer.write(chunk)
                except requests.exceptions.RequestException as e:
                    printLOG(1," Error downloading fast_align.exe: {e}")
            
            
            fast_align = os.path.join(build_root, 'fast_align.exe')
        elif platform.system()=="Darwin":
            url = 'https://github.com/mtuoc/MTUOC-server/releases/download/v202511/fast_alignMAC'
            nom_fitxer = 'fast_alignMAC'
            ruta_fitxer = Path(nom_fitxer)
            if not ruta_fitxer.exists():
                try:
                    resposta = requests.get(url, stream=True)
                    resposta.raise_for_status()
                    with open(ruta_fitxer, 'wb') as fitxer:
                        for chunk in resposta.iter_content(chunk_size=8192):
                            if chunk:
                                fitxer.write(chunk)
                    st = os.stat(ruta_fitxer)
                    os.chmod(ruta_fitxer, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except requests.exceptions.RequestException as e:
                    printLOG(1," Error downloading fast_alignMAC: {e}")
                except OSError as e:
                    printLOG(1, "Error changing permissions to fast_alignMAC: {e}")
            fast_align = os.path.join(build_root, 'fast_alignMAC')

        else:
            url = 'https://github.com/mtuoc/MTUOC-server/releases/download/v202511/fast_align'
            nom_fitxer = 'fast_align'
            ruta_fitxer = Path(nom_fitxer)
            if not ruta_fitxer.exists():
                try:
                    resposta = requests.get(url, stream=True)
                    resposta.raise_for_status()
                    with open(ruta_fitxer, 'wb') as fitxer:
                        for chunk in resposta.iter_content(chunk_size=8192):
                            if chunk:
                                fitxer.write(chunk)
                    st = os.stat(ruta_fitxer)
                    os.chmod(ruta_fitxer, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except requests.exceptions.RequestException as e:
                    printLOG(1," Error downloading fast_align: {e}")
                except OSError as e:
                    printLOG(1, "Error changing permissions to fast_align: {e}")
            fast_align = os.path.join(build_root, 'fast_align')
        
        
        
        if platform.system()=="Windows":
            url = 'https://github.com/mtuoc/MTUOC-server/releases/download/v202511/atools.exe'
            nom_fitxer = 'atools.exe'
            ruta_fitxer = Path(nom_fitxer)
            if not ruta_fitxer.exists():
                try:
                    resposta = requests.get(url, stream=True)
                    resposta.raise_for_status()
                    with open(ruta_fitxer, 'wb') as fitxer:
                        for chunk in resposta.iter_content(chunk_size=8192):
                            if chunk:
                                fitxer.write(chunk)
                except requests.exceptions.RequestException as e:
                    printLOG(1," Error downloading atools.exe: {e}")
            atools = os.path.join(build_root, 'atools.exe')
                
        elif platform.system()=="Darwin":
            url = 'https://github.com/mtuoc/MTUOC-server/releases/download/v202511/atoolsMAC'
            nom_fitxer = 'atoolsMAC'
            ruta_fitxer = Path(nom_fitxer)
            if not ruta_fitxer.exists():
                try:
                    resposta = requests.get(url, stream=True)
                    resposta.raise_for_status()
                    with open(ruta_fitxer, 'wb') as fitxer:
                        for chunk in resposta.iter_content(chunk_size=8192):
                            if chunk:
                                fitxer.write(chunk)
                    st = os.stat(ruta_fitxer)
                    os.chmod(ruta_fitxer, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except requests.exceptions.RequestException as e:
                    printLOG(1," Error downloading atoolsMAC: {e}")
                except OSError as e:
                    printLOG(1, "Error changing permissions to atoolsMAC: {e}")
            atools = os.path.join(build_root, 'atoolsMAC')

        else:
            url = 'https://github.com/mtuoc/MTUOC-server/releases/download/v202511/atools'
            nom_fitxer = 'atools'
            ruta_fitxer = Path(nom_fitxer)
            if not ruta_fitxer.exists():
                try:
                    resposta = requests.get(url, stream=True)
                    resposta.raise_for_status()
                    with open(ruta_fitxer, 'wb') as fitxer:
                        for chunk in resposta.iter_content(chunk_size=8192):
                            if chunk:
                                fitxer.write(chunk)
                        st = os.stat(ruta_fitxer)
                        os.chmod(ruta_fitxer, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                except requests.exceptions.RequestException as e:
                    printLOG(1," Error downloading atools: {e}")
                except OSError as e:
                    printLOG(1, "Error changing permissions to atools: {e}")
            atools = os.path.join(build_root, 'atools')

        (fwd_T, fwd_m) = self.read_err(fwd_err)
        (rev_T, rev_m) = self.read_err(rev_err)

        self.fwd_cmd = [fast_align, '-i', '-', '-d', '-T', fwd_T, '-m', fwd_m, '-f', fwd_params]
        self.rev_cmd = [fast_align, '-i', '-', '-d', '-T', rev_T, '-m', rev_m, '-f', rev_params, '-r']
        self.tools_cmd = [atools, '-i', '-', '-j', '-', '-c', heuristic]

        self.fwd_align =  self.popen_io(self.fwd_cmd)
        self.rev_align =  self.popen_io(self.rev_cmd)
        self.tools = self.popen_io(self.tools_cmd)

        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.src_tokenizer = None #config.GetWordAlignments_tokenizerSL #MosesTokenizer(lang=self.src_lang)
        self.tgt_tokenizer = None #config.GetWordAlignments_tokenizerTL #MosesTokenizer(lang=self.tgt_lang)
    
    def set_src_tokenizer(self, tokenizer):
        self.src_tokenizer=tokenizer
        
    def set_tgt_tokenizer(self, tokenizer):
        self.tgt_tokenizer=tokenizer
    '''
    def align(self, line):
        try:
            self.fwd_align.stdin.write('{}\n'.format(line))
            self.rev_align.stdin.write('{}\n'.format(line))
            self.fwd_align.stdin.flush()
            self.rev_align.stdin.flush()
        except BrokenPipeError:
            print("Broken pipe encountered when writing to fast_align subprocess", sys.exc_info())
            return None

        fwd_line = self.fwd_align.stdout.readline().split('|||')[2].strip()
        rev_line = self.rev_align.stdout.readline().split('|||')[2].strip()
        self.tools.stdin.write('{}\n'.format(fwd_line))
        self.tools.stdin.write('{}\n'.format(rev_line))
        self.tools.stdin.flush()

        al_line = self.tools.stdout.readline().strip()
        return al_line
    
    '''
    
    def start_subprocesses(self):
        print("Starting subprocesses...", file=sys.stderr)
        self.fwd_align =  self.popen_io(self.fwd_cmd)
        self.rev_align =  self.popen_io(self.rev_cmd)
        self.tools = self.popen_io(self.tools_cmd)

    def restart_subprocesses(self):
        print("Restarting subprocesses...", file=sys.stderr)
        self.close()
        self.start_subprocesses()
        
    def _subprocesses_alive(self):
        """Check if all subprocesses are alive."""
        processes = [self.fwd_align, self.rev_align, self.tools]
        return all(proc and proc.poll() is None for proc in processes)
    
    def align(self, line):
        '''
        try:
            self.fwd_align.stdin.write('{}\n'.format(line))
            self.rev_align.stdin.write('{}\n'.format(line))
            ###
            self.fwd_align.stdin.flush()
            self.rev_align.stdin.flush()
            ###
        except BrokenPipeError:
            print("Broken pipe encountered when writing to fast_align subprocess", sys.exc_info())#file=sys.stderr)
            return None
        '''
        if not self._subprocesses_alive():
            print("Subprocesses not running. Restarting...", file=sys.stderr)
            self.restart_subprocesses()
        self.fwd_align.stdin.write('{}\n'.format(line))
        self.rev_align.stdin.write('{}\n'.format(line))
        ###
        self.fwd_align.stdin.flush()
        self.rev_align.stdin.flush()
        
        # f words ||| e words ||| links ||| score
        fwd_line = self.fwd_align.stdout.readline().split('|||')[2].strip()
        rev_line = self.rev_align.stdout.readline().split('|||')[2].strip()
        self.tools.stdin.write('{}\n'.format(fwd_line))
        self.tools.stdin.write('{}\n'.format(rev_line))
        ###
        self.tools.stdin.flush()
        ###
        al_line = self.tools.stdout.readline().strip()
        time.sleep(0.1)
        return al_line
 
    def close(self):
        self.fwd_align.stdin.close()
        self.fwd_align.wait()
        self.rev_align.stdin.close()
        self.rev_align.wait()
        self.tools.stdin.close()
        self.tools.wait()

    def read_err(self, err):
        (T, m) = ('', '')
        for line in open(err):
            # expected target length = source length * N
            if 'expected target length' in line:
                m = line.split()[-1]
            # final tension: N
            elif 'final tension' in line:
                T = line.split()[-1]
        return (T, m)

    def align_sentence_pair(self,source,target):
        
        '''
        Method to aling a pair of sentences.
        * Parameters:
            * source: Source sentence as a string.
            * target: Target sentence as a string.
        * Return:
            * String containing the alignment using Pharao format.
        '''
        if not self.src_tokenizer==None:
            sourceL = self.src_tokenizer.tokenize(source.strip())
        else:
            sourceL=source.strip()
        if not self.tgt_tokenizer==None:    
            targetL = self.tgt_tokenizer.tokenize(target.strip())
        else:
            targetL=target.strip()

        #source = ' '.join(source)
        #target = ' '.join(target)
        
        source=sourceL
        target=targetL

        line = ' ||| '.join([source,target])
        alignment = self.align(line)
        return alignment,sourceL,targetL

    
    def popen_io(self, cmd):
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
        def consume(s):
            for _ in s:
                pass
        #threading.Thread(target=consume, args=(p.stdout,)).start()
        threading.Thread(target=consume, args=(p.stderr,)).start()
        return p

def popen_io(cmd):
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
    def consume(s):
        for _ in s:
            pass
    threading.Thread(target=consume, args=(p.stderr,)).start()
    return p

