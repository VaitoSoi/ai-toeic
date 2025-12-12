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

export interface Topic {
    id: string

    type: "writing"
    part: "2" | "3"
    question: string
    summary?: Summary
    created_at: string

    submissions: Submission[]
    reviews: Review[]
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
    replacement: string | undefined
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

    status: | "reviewing" | "failed" | "done",

    score_range: [number, number] | undefined
    level_achieved: number | undefined
    overall_feedback: string | undefined
    summary_feedback: string | undefined
    detail_score: DetailScore | undefined
    annotations: ReviewAnnotation[] | undefined

    created_at: string
}
