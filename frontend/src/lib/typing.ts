export interface Statistics {
    total_submission: number,
    average_score: number
    improvement_rate: number
    total_time: number
}


export interface Summary {
    summary: string
    description: string
}

export type Status = "pending" | "failed" | "done";

export interface Topic {
    id: string

    status: Status

    type: "writing"
    part: "2" | "3"

    question?: string
    question_set?: TopicQuestion[]

    summary?: Summary
    created_at: string

    submissions: Submission[]
    reviews: Review[]
}

export interface TopicQuestion {
    id: string
    topic_id: string
    artist_prompt: string
    file: string
    keywords: [string, string]
    created_at: string
}

export interface Submission {
    id: string
    topic_id: string
    submission: string
    review?: Review
    created_at: string
}


export interface ReviewAnnotation {
    target_text: string
    context_before: string
    type: "grammar" | "vocabulary" | "coherence" | "mechanics"
    replacement?: string
    feedback: string
}

export interface DetailScore {
    grammar: number
    vocabulary: number
    organization: number
    task_fulfillment: number
}

export interface Review {
    id: string

    topic_id: string
    submission_id: string

    status: Status,

    score_range?: [number, number]
    level_achieved?: number
    overall_feedback?: string
    summary_feedback?: string
    detail_score?: DetailScore
    annotations?: ReviewAnnotation[]
    improvement_suggestions?: string[]

    created_at: string
}
