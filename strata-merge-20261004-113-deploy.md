# Strata merge-forks-20261004 ｜ 113 离线部署说明

分支 `merge-forks-20261004` = 上游 0.1.38 (99f3dbd) + 17 个未合并二开 PR + 1 个 cherry-pick。
本机（3090 单卡）已完成编译 + ctest + A/B 测速（见根目录 bench-merge-result-*.json）。
113 SSH（zuiyi-server-6-tail / 100.101.185.37）当前不通，恢复后按下面步骤部署。

## 携带文件

- `strata-merge-20261004-tree.tar.gz` —— 分支全量源码树（serve/ + src/ + 工具，15.5 MB）
- `strata-merge-20261004-ggml.tar.gz` —— 编译所用的 ggml 源码（解出为 `llama.cpp/ggml`，3.2 MB）

## 部署步骤（113）

```bash
# 0) 传输（本机 → 113，或 U 盘/网盘中转）
scp strata-merge-20261004-*.tar.gz zuiyi-server-6-tail:/tmp/

# 1) 备份现役 Strata 目录里会被覆盖的东西（配置/数据本来就在 Strata-data，不受影响）
cp -a ~/Strata ~/Strata.bak-merge 2>/dev/null || true

# 2) 解包源码树到 Strata 目录（覆盖 serve/ src/ 等，不动 Strata-data / engine 二进制）
mkdir -p /tmp/strata-tree && tar xzf /tmp/strata-merge-20261004-tree.tar.gz -C /tmp/strata-tree
rsync -a /tmp/strata-tree/ ~/Strata/        # 或先解到新目录 ~/Strata-merge

# 3) 编译引擎（sm_75）
mkdir -p /opt/strata-ggml && tar xzf /tmp/strata-merge-20261004-ggml.tar.gz -C /opt/strata-ggml
cd ~/Strata
cmake -G Ninja -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DSTRATA_ENABLE_CUDA=ON -DSTRATA_BUILD_TESTS=OFF \
  -DCMAKE_CUDA_ARCHITECTURES=75-real \
  -DSTRATA_GGML_DIR=/opt/strata-ggml/llama.cpp
cmake --build build --target strata -j $(nproc)
cp build/strata.exe engine/strata-merged.exe    # 引擎 exe 在 Linux 同名

# 4)（可选但推荐）跑测试：-DSTRATA_BUILD_TESTS=ON 重新 configure 后
#    cmake --build build -j && ctest --output-on-failure

# 5) 换配置试跑：复制现役启动 config，把 "exe" 指到 engine/strata-merged.exe、log 另起名，
#    端口错开（如 8081）先冒烟，确认日志行正常再切主配置。
#    层分割 [0,1] 与 kv-resident 32768 参数不变。

# 6) 新引擎相关开关（均为默认行为，无需改参数）：
#    - STRATA_FILL_AHEAD（#699 映射加载预读，默认 256 对，设 0 关闭）
#    - Linux THP 专家 arena（#650，系统需 transparent_hugepage/enabled=madvise+ 才生效）
#    - STRATA_POOL_QUANT_THRESH（#500 CPU 池量化并行阈值，默认 max(8, workers)）
#    - STRATA_NO_LARGEPAGES / 大页：见 2026-10-04 本机 2MB pin 备忘（113 是 Linux，走 THP 路径）
```

## 回滚

引擎 exe 未覆盖原文件（新二进制叫 strata-merged.exe，原 strata.exe 原样）；源码覆盖前有 `~/Strata.bak-merge`。

## 2026-10-04 深夜补遗：merged 引擎在 113 的实测结论与切换要求

- **生产切换（113）必须带 `--vram-reserve-mib 1200`**：merged 引擎（#584 carve+缓存吃满 + #646 更大 MTP round 图）会把草稿卡余量榨干，384 时首请求即 `mtp: round capture: instantiate=out of memory` 崩溃（老引擎同配置正常）。若见此错误先查 reserve。instantiate 失败时错误信息会打印 EndCapture 的 "no error"——真实原因要 cudaGetLastError()（诊断补丁在 113 worktree mtp.cpp，未回传本地分支）。
- **113 双 T10 [1,2] 层分割 A/B（reserve 1200 两臂同配置）**：decode 8K +12.8%（42.6→48.1）/ 64K +17.2%（41.9→49.1）；prefill 8K +21.5% / 64K +31.7%（1225→1614）；probe 逐字节一致，逐轮分布零重叠。新引擎@1200（缓存更小）仍胜旧引擎@384 的 46-48 t/s。
- 单卡 T10：decode +2~3%、prefill +24.7/+33.1%（#742/#655/#693 的 sm_75 收益兑现）。STRATA_POOL_PIPELINE=1（#733）在 113 真 CPU 瓶颈上=噪声，#733 最终出局。#743 TOPK_STREAM 需 200K payload 才过阈值，未测。
- 部署形态：/data3t/strata-deploy/Strata-final（worktree，bundle 增量传输）；bench-113.py（已修 Linux killpg/venv 软链/api_key 鉴权三坑）；NGFF 盘在 C220 第二 M.2 槽无 SATA 走线不可用，模型走 USB 盒（SC311 128G→/mnt/model-ssd）。
