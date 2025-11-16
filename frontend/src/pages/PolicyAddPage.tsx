import React, { useState, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Progress } from '@/components/ui/progress'
import { Upload, X, FileText, Image as ImageIcon } from 'lucide-react'
import { toast } from 'sonner'
import { uploadPolicy, pollTaskStatus } from '@/lib/api'

interface PolicyAddPageProps {
  onBack?: () => void
  onSuccess?: () => void
}

export const PolicyAddPage: React.FC<PolicyAddPageProps> = ({ onBack, onSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    authority: '',
    description: '',
  })
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }, [])

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (file: File) => {
    // 파일 크기 체크 (50MB)
    if (file.size > 50 * 1024 * 1024) {
      alert('파일 크기는 50MB를 초과할 수 없습니다')
      return
    }

    // 파일 형식 체크
    const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
    if (!validTypes.includes(file.type)) {
      alert('지원하지 않는 파일 형식입니다. PDF 또는 이미지 파일을 선택하세요')
      return
    }

    setSelectedFile(file)
  }

  const removeFile = () => {
    setSelectedFile(null)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedFile) {
      toast.error('파일을 선택해주세요')
      return
    }

    if (!formData.title || !formData.authority) {
      toast.error('필수 항목을 모두 입력해주세요')
      return
    }

    setIsUploading(true)
    setUploadProgress(0)

    // Toast 알림으로 업로드 시작
    const uploadToastId = toast.loading('파일 업로드 중...', {
      description: '정책 문서를 서버에 업로드하고 있습니다.',
    })

    try {
      // 1단계: 파일 업로드
      setUploadProgress(10)
      const uploadResult = await uploadPolicy(
        selectedFile,
        formData.title,
        formData.authority,
        formData.description
      )

      setUploadProgress(30)
      toast.success('파일 업로드 완료!', {
        id: uploadToastId,
        description: `${uploadResult.processing_method}로 텍스트를 추출했습니다.`,
      })

      // 2단계: 백그라운드 작업이 있는 경우 진행률 추적
      if (uploadResult.task_id) {
        const processingToastId = toast.loading('멀티모달 처리 중...', {
          description: 'AI가 정책 가이드라인을 추출하고 VectorDB에 임베딩하고 있습니다.',
        })

        // Task 상태 폴링
        await pollTaskStatus(
          uploadResult.task_id,
          (progress, message) => {
            setUploadProgress(30 + (progress * 0.7)) // 30%부터 100%까지
            toast.loading(`처리 진행 중: ${progress}%`, {
              id: processingToastId,
              description: message,
            })
          },
          2000 // 2초마다 폴링
        )

        toast.success('정책 처리 완료!', {
          id: processingToastId,
          description: '가이드라인 추출 및 VectorDB 임베딩이 완료되었습니다.',
          duration: 5000,
        })
      }

      setUploadProgress(100)

      // 성공 메시지
      toast.success('정책이 성공적으로 등록되었습니다!', {
        description: `"${formData.title}" 정책이 시스템에 추가되었습니다.`,
        duration: 5000,
      })

      // 폼 초기화
      setSelectedFile(null)
      setFormData({ title: '', authority: '', description: '' })

      // 성공 콜백
      onSuccess?.()
    } catch (error) {
      console.error('Upload error:', error)
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다'
      toast.error('정책 등록 실패', {
        description: errorMessage,
        duration: 5000,
      })
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  return (
    <div className="container mx-auto max-w-4xl p-6">
      <div className="mb-6">
        {onBack && (
          <Button variant="outline" onClick={onBack} className="mb-4">
            ← 목록으로 돌아가기
          </Button>
        )}
        <h1 className="text-3xl font-bold">정책 추가</h1>
        <p className="text-muted-foreground">정책 문서를 업로드하고 정보를 입력하세요</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 파일 업로드 영역 */}
        <Card>
          <CardContent className="pt-6">
            <div
              className={`relative border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                dragActive
                  ? 'border-primary bg-primary/5'
                  : 'border-muted-foreground/25 hover:border-primary/50'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                id="fileInput"
                className="hidden"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleFileInput}
                disabled={isUploading}
              />
              <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                정책 문서를 드래그하거나 클릭하여 업로드
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                지원 형식: PDF, PNG, JPG, JPEG (최대 50MB)
              </p>
              <Button
                type="button"
                onClick={() => document.getElementById('fileInput')?.click()}
                disabled={isUploading}
              >
                파일 선택
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 선택된 파일 미리보기 */}
        {selectedFile && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">선택된 파일</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                <div className="flex items-center gap-4">
                  {selectedFile.type === 'application/pdf' ? (
                    <FileText className="h-8 w-8 text-primary" />
                  ) : (
                    <ImageIcon className="h-8 w-8 text-primary" />
                  )}
                  <div>
                    <div className="font-medium">{selectedFile.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {formatFileSize(selectedFile.size)}
                    </div>
                  </div>
                </div>
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={removeFile}
                  disabled={isUploading}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 정책 정보 입력 */}
        <Card>
          <CardHeader>
            <CardTitle>정책 정보</CardTitle>
            <CardDescription>정책에 대한 상세 정보를 입력하세요</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">정책 제목 *</Label>
              <Input
                id="title"
                placeholder="예: 개인정보 처리 방침 2024"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
                disabled={isUploading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="authority">발행 기관 *</Label>
              <Select
                value={formData.authority || undefined}
                onValueChange={(value) => setFormData({ ...formData, authority: value })}
                disabled={isUploading}
              >
                <SelectTrigger id="authority">
                  <SelectValue placeholder="선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="내부">내부 정책</SelectItem>
                  <SelectItem value="개인정보보호위원회">개인정보보호위원회</SelectItem>
                  <SelectItem value="금융보안원">금융보안원</SelectItem>
                  <SelectItem value="금융위원회">금융위원회</SelectItem>
                  <SelectItem value="공정거래위원회">공정거래위원회</SelectItem>
                  <SelectItem value="KISA">KISA (한국인터넷진흥원)</SelectItem>
                  <SelectItem value="기타">기타</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">정책 설명</Label>
              <Textarea
                id="description"
                placeholder="정책에 대한 간단한 설명을 입력하세요"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                disabled={isUploading}
                rows={4}
              />
            </div>
          </CardContent>
        </Card>

        {/* 업로드 진행률 */}
        {isUploading && (
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>정책 문서를 처리하고 있습니다...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} />
                <p className="text-xs text-muted-foreground text-center">
                  파일 크기에 따라 시간이 소요될 수 있습니다
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 제출 버튼 */}
        <div className="flex justify-center gap-4">
          <Button type="button" variant="outline" onClick={onBack} disabled={isUploading}>
            취소
          </Button>
          <Button type="submit" size="lg" disabled={isUploading}>
            {isUploading ? '등록 중...' : '정책 등록'}
          </Button>
        </div>
      </form>
    </div>
  )
}
