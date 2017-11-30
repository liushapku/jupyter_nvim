
command! -nargs=+ -range -bang Jupyter call Jupyter({
      \ 'cmd': 1,
      \ 'bang':  <bang>0,
      \ 'line1': <line1>,
      \ 'line2': <line2>,
      \ 'count': <count>,
      \ 'mods':  <q-mods>}, <q-args>)

nmap <leader>E :<c-u>exe printf(".,+%dJupyter run", v:count1-1)<cr>
