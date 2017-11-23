let SessionLoad = 1
let s:so_save = &so | let s:siso_save = &siso | set so=0 siso=0
let v:this_session=expand("<sfile>:p")
silent only
exe "cd " . escape(expand("<sfile>:p:h"), ' ')
if expand('%') == '' && !&modified && line('$') <= 1 && getline(1) == ''
  let s:wipebuf = bufnr('%')
endif
set shortmess=aoO
badd +185 ~/repos/jupyter_container/application.py
badd +298 ~/repos/nvim/bundle/nvim-ipy/rplugin/python3/nvim_ipy/__init__.py
badd +231 ~/miniconda3/lib/python3.6/site-packages/jupyter_client/threaded.py
badd +265 ~/miniconda3/lib/python3.6/site-packages/jupyter_client/client.py
badd +230 ~/miniconda3/lib/python3.6/site-packages/jupyter_core/application.py
badd +133 nvimapp.py
badd +19 test/nvim.py
badd +33 ~/miniconda3/lib/python3.6/site-packages/jupyter_client/channelsabc.py
badd +162 ~/miniconda3/lib/python3.6/site-packages/jupyter_client/channels.py
badd +114 ~/miniconda3/lib/python3.6/site-packages/jupyter_client/consoleapp.py
badd +1617 ~/miniconda3/lib/python3.6/site-packages/traitlets/traitlets.py
badd +25 ~/repos/jupyter_container/kernelmanager.py
badd +176 ~/miniconda3/lib/python3.6/site-packages/zmq/eventloop/zmqstream.py
badd +29 __init__.py
badd +131 ~/miniconda3/lib/python3.6/site-packages/neovim/api/buffer.py
badd +3 ~/.local/share/nvim/rplugin.vim
badd +39 ~/repos/dotfiles/shell/bin.link/nvim-embed
badd +1 test/test.py
badd +0 ~/repos/nvim/vim.dotlink/x.vim
argglobal
silent! argdel *
argadd ~/repos/jupyter_container/application.py
edit ~/repos/nvim/vim.dotlink/x.vim
set splitbelow splitright
wincmd _ | wincmd |
vsplit
1wincmd h
wincmd w
wincmd _ | wincmd |
split
1wincmd k
wincmd w
set nosplitbelow
set nosplitright
wincmd t
set winminheight=1 winminwidth=1 winheight=1 winwidth=1
exe 'vert 1resize ' . ((&columns * 95 + 137) / 275)
exe '2resize ' . ((&lines * 9 + 26) / 52)
exe 'vert 2resize ' . ((&columns * 179 + 137) / 275)
exe '3resize ' . ((&lines * 38 + 26) / 52)
exe 'vert 3resize ' . ((&columns * 179 + 137) / 275)
argglobal
setlocal fdm=manual
setlocal fde=0
setlocal fmr={{{,}}}
setlocal fdi=#
setlocal fdl=0
setlocal fml=1
setlocal fdn=20
setlocal fen
silent! normal! zE
let s:l = 28 - ((27 * winheight(0) + 24) / 48)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
28
normal! 023|
wincmd w
argglobal
edit /usr/share/nvim/runtime/doc/api.txt
setlocal fdm=manual
setlocal fde=0
setlocal fmr={{{,}}}
setlocal fdi=#
setlocal fdl=0
setlocal fml=1
setlocal fdn=20
setlocal nofen
silent! normal! zE
let s:l = 472 - ((2 * winheight(0) + 4) / 9)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
472
normal! 045|
wincmd w
argglobal
edit test/nvim.py
setlocal fdm=manual
setlocal fde=0
setlocal fmr={{{,}}}
setlocal fdi=#
setlocal fdl=0
setlocal fml=1
setlocal fdn=20
setlocal fen
silent! normal! zE
let s:l = 18 - ((9 * winheight(0) + 19) / 38)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
18
normal! 0
wincmd w
exe 'vert 1resize ' . ((&columns * 95 + 137) / 275)
exe '2resize ' . ((&lines * 9 + 26) / 52)
exe 'vert 2resize ' . ((&columns * 179 + 137) / 275)
exe '3resize ' . ((&lines * 38 + 26) / 52)
exe 'vert 3resize ' . ((&columns * 179 + 137) / 275)
tabnext 1
if exists('s:wipebuf') && getbufvar(s:wipebuf, '&buftype') isnot# 'terminal'
  silent exe 'bwipe ' . s:wipebuf
endif
unlet! s:wipebuf
set winheight=1 winwidth=20 winminheight=1 winminwidth=1 shortmess=filnxtToOc
let s:sx = expand("<sfile>:p:r")."x.vim"
if file_readable(s:sx)
  exe "source " . fnameescape(s:sx)
endif
let &so = s:so_save | let &siso = s:siso_save
doautoall SessionLoadPost
unlet SessionLoad
" vim: set ft=vim :
