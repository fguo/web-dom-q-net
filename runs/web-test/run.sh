cd ../..
python exec.py official webtestjune  \
    settings/medium3tasks_cpu_saveckpt.json  \
    --paths paths/webtest.json  \
    --hparams hparams/nn/multitask_vocab600.json  \
    hparams/qlearn/ddqn_nsteps_multitask.json   \
    hparams/replay_buffer/multitask_prioritized100000.json  \
    hparams/graph/3.json   \
    hparams/dom/goal_attn_cat_large_V.json   \
    --reset
cd -


