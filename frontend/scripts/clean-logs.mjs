import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const RETENTION_DAYS = Number(process.env.LOG_RETENTION_DAYS ?? 7)
const FRONTEND_ROOT = path.resolve(__dirname, '..')
const LOGS_DIR = path.join(FRONTEND_ROOT, 'logs')

// logs/ 디렉토리가 없으면 생성
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR, { recursive: true })
}

let movedCount = 0
let deletedCount = 0

// 1) frontend/ 루트의 *.log 파일을 logs/ 로 이동
const rootEntries = fs.readdirSync(FRONTEND_ROOT)
for (const entry of rootEntries) {
  if (!entry.endsWith('.log')) continue

  const src = path.join(FRONTEND_ROOT, entry)
  if (!fs.statSync(src).isFile()) continue

  let dest = path.join(LOGS_DIR, entry)

  // 동명 파일이 이미 logs/ 에 있으면 타임스탬프 접미사 부여
  if (fs.existsSync(dest)) {
    const ts = new Date().toISOString().replace(/[:.]/g, '-')
    const ext = path.extname(entry)
    const base = path.basename(entry, ext)
    dest = path.join(LOGS_DIR, `${base}-${ts}${ext}`)
  }

  fs.renameSync(src, dest)
  movedCount++
}

// 2) logs/ 안의 *.log 파일 중 보존 기간 초과 파일 삭제
const cutoff = Date.now() - RETENTION_DAYS * 24 * 60 * 60 * 1000
const logsEntries = fs.readdirSync(LOGS_DIR)
for (const entry of logsEntries) {
  if (!entry.endsWith('.log')) continue

  const filePath = path.join(LOGS_DIR, entry)
  const stat = fs.statSync(filePath)
  if (!stat.isFile()) continue

  if (stat.mtimeMs < cutoff) {
    fs.unlinkSync(filePath)
    deletedCount++
  }
}

console.log(`[clean-logs] 이동: ${movedCount}개, 삭제(${RETENTION_DAYS}일 초과): ${deletedCount}개`)
