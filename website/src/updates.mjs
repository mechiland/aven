import { readFileSync } from 'node:fs';

export const update = JSON.parse(readFileSync(new URL('../public/updates.json', import.meta.url), 'utf8'));
if (update.status !== 'published' || !/^https:\/\//.test(update.url)
  || !/^[a-f0-9]{64}$/.test(update.sha256) || !Number.isSafeInteger(update.bytes) || update.bytes <= 0) {
  throw new Error('Online installer requires verified, complete publication metadata.');
}

export const updateCopy = {
  'zh-cn': {
    title: '在现有系统上，加入 Aven。', label: '在线安装 · 0.4.0',
    intro: '适用于 Fedora Kinoite 44 x86_64，也支持将已有 Aven ISO 安装接入更新通道。',
    download: '下载在线安装器', guide: '安装与更新指南', metadata: '安装器校验信息',
    scope: '当前仅支持 Kinoite 44 x86_64。首次安装包含 Plasma 6.8 Beta 依赖，可能下载约 440 MB 系统包及缺少的应用、字体。',
    features: [
      ['只下载变化的组件', '后续主题与应用集成更新复用本地缓存，无需重新下载 ISO。'],
      ['保留自己的习惯', '常规更新保留面板布局、固定应用、文件夹视图、账户、书签与个人文件。'],
      ['验证后再应用', '更新组件经过签名与校验验证，支持中断恢复和上一版 Aven 配置回滚。'],
    ],
    install: '首次安装，或接入已有 Aven',
    before: '先核对安装器 SHA-256。关闭文件、浏览器、邮件、照片与预览，在 Konsole 中以当前桌面用户执行，不要在安装命令前加 sudo。',
    reboot: '若提示已暂存依赖，请重启后运行以下命令完成安装；完成后注销并重新登录。',
    routine: '之后，按需更新', commands: ['查看可用版本、变化组件与下载量', '只下载并验证，暂不应用', '应用更新前先关闭上述应用', '查看当前版本与恢复状态'],
    defaults: '常规更新保留你已有的布局。要切换为截图中的全宽底栏等新版默认设置，可明确执行 aven update --reset-defaults；这会重新应用默认布局与设置。',
    recovery: '更新中断，或想回到上一版？',
    recoveryIntro: '先关闭应用并注销 Plasma，再从文本控制台（Ctrl + Alt + F3）或 SSH 执行恢复，避免运行中的应用覆盖恢复结果。',
    recover: '恢复中断的应用过程', rollback: '恢复上一版 Aven 配置与资源',
    recoveryNote: '恢复时会检查后续修改，遇到冲突会报告。Aven 配置回滚与 Fedora 系统部署回滚分开；系统与安全更新仍通过 Discover 或 rpm-ostree 完成。',
    proof: '已验证：从官方 Kinoite 基线安装、依赖暂存与重启、组件升级、设置与数据保留、中断恢复及配置回滚。一次仅主题更新测试下载了 20,749 字节；实际大小取决于变化的组件。',
    proofLink: '查看更新验证记录', proofImage: '查看在线安装后的中文界面',
    proofAlt: '在线安装验证中的真实中文 Dolphin 窗口，列表包含更新保留文档.txt，底部为全宽面板',
    proofCaption: '在线安装验证 · 原始 1440 × 900 截图 · 中文界面与更新后保留的文档',
    isoTitle: '从零开始，也可以用 ISO。', isoIntro: '离线安装镜像仍为 Union 0.3.1。安装后可使用上方安装器接入 0.4.0 更新通道；ISO 本身未重建为最新底栏版本。',
    panelNote: 'round 08 布局实机记录。在线安装使用新版默认布局；已有安装的常规更新保留原布局。',
  },
  en: {
    title: 'Add Aven to the system you have.', label: 'ONLINE INSTALL · 0.4.0',
    intro: 'For Fedora Kinoite 44 x86_64. Existing Aven ISO installations can join the same update channel.',
    download: 'Download online installer', guide: 'Install & update guide', metadata: 'Installer verification details',
    scope: 'Currently supports Kinoite 44 x86_64 only. Initial setup includes Plasma 6.8 Beta and may download roughly 440 MB of system packages, plus missing apps and fonts.',
    features: [
      ['Download what changed', 'Later theme and app integration updates reuse cached components. No new ISO download is needed.'],
      ['Keep your preferences', 'Routine updates retain panel layouts, pinned apps, folder views, accounts, bookmarks and personal files.'],
      ['Verify before applying', 'Signed components are verified before use, with interrupted-update recovery and rollback to the previous Aven profile.'],
    ],
    install: 'Install, or adopt an existing Aven system',
    before: 'Check the installer SHA-256 first. Close Files, Browser, Mail, Photos and Preview. Run in Konsole as your desktop user; do not prefix the installer command with sudo.',
    reboot: 'If dependencies are staged, reboot and finish with the command below. Log out and back in after installation completes.',
    routine: 'Update when you’re ready', commands: ['Check the version, changed components and download size', 'Download and verify without applying', 'Close the apps listed above before applying', 'View installed version and recovery state'],
    defaults: 'Routine updates keep your layout. To adopt new defaults, including the full-width panel shown here, explicitly run aven update --reset-defaults. This reapplies the default layout and settings.',
    recovery: 'Interrupted update, or want to go back?',
    recoveryIntro: 'Close apps and log out of Plasma first. Use a text console (Ctrl + Alt + F3) or SSH so running apps cannot overwrite restored settings.',
    recover: 'Recover an interrupted application', rollback: 'Restore the previous Aven profile and assets',
    recoveryNote: 'Recovery checks for later edits and reports conflicts. Aven profile rollback is separate from Fedora deployment rollback. System and security updates remain in Discover or rpm-ostree.',
    proof: 'Verified: installation from the official Kinoite baseline, dependency staging and reboot, component upgrades, settings and data preservation, interrupted-apply recovery and profile rollback. One theme-only test downloaded 20,749 bytes; actual sizes depend on the changed components.',
    proofLink: 'Read update verification', proofImage: 'See Chinese UI after online installation',
    proofAlt: 'Real Chinese Dolphin UI from online installation verification, with the preserved document 更新保留文档.txt and a full-width bottom panel',
    proofCaption: 'Online installation verification · Original 1440 × 900 capture · Chinese UI and a preserved document',
    isoTitle: 'Starting fresh? There’s an ISO, too.', isoIntro: 'The offline installer remains Union 0.3.1. After installation, use the online installer above to join the 0.4.0 channel. The ISO has not been rebuilt with the latest panel.',
    panelNote: 'Native round 08 layout capture. Online installation uses the new defaults; routine updates of existing installations retain their layout.',
  },
};
