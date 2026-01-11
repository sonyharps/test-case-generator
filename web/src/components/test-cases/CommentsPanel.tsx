import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { MessageCircle, Send, Reply, CheckCircle } from "lucide-react";
import {
  getComments,
  addComment,
  resolveComment,
  type Comment,
} from "@/api/testCases";
import { useAuth } from "@/store/auth.store";

interface CommentsPanelProps {
  testCaseId: number;
}

function CommentItem({
  comment,
  testCaseId,
  onReply,
  onResolve,
  depth = 0,
}: {
  comment: Comment;
  testCaseId: number;
  onReply: (commentId: number) => void;
  onResolve: () => void;
  depth?: number;
}) {
  const accessToken = useAuth((state) => state.accessToken);
  const [resolving, setResolving] = useState(false);

  const handleResolve = async () => {
    setResolving(true);
    try {
      await resolveComment(testCaseId, comment.id, accessToken!);
      onResolve();
    } catch (err) {
      console.error("Failed to resolve comment:", err);
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className={`${depth > 0 ? "ml-8 mt-3" : ""}`}>
      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium text-sm">
              {comment.user_name.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-medium text-sm text-gray-900">{comment.user_name}</p>
              <p className="text-xs text-gray-500">
                {new Date(comment.created_at).toLocaleString()}
              </p>
            </div>
          </div>
          {comment.is_resolved && (
            <Badge className="bg-green-100 text-green-800 border-green-200">
              <CheckCircle className="w-3 h-3 mr-1" />
              Resolved
            </Badge>
          )}
        </div>

        <p className="text-sm text-gray-700 whitespace-pre-wrap mb-3">
          {comment.comment_text}
        </p>

        <div className="flex gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onReply(comment.id)}
            className="text-xs"
          >
            <Reply className="w-3 h-3 mr-1" />
            Reply
          </Button>
          {!comment.is_resolved && (
            <Button
              size="sm"
              variant="ghost"
              onClick={handleResolve}
              disabled={resolving}
              className="text-xs text-green-600 hover:text-green-700"
            >
              <CheckCircle className="w-3 h-3 mr-1" />
              {resolving ? "Resolving..." : "Mark Resolved"}
            </Button>
          )}
        </div>
      </div>

      {/* Render replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-3">
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              testCaseId={testCaseId}
              onReply={onReply}
              onResolve={onResolve}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function CommentsPanel({ testCaseId }: CommentsPanelProps) {
  const accessToken = useAuth((state) => state.accessToken);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState("");
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadComments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getComments(testCaseId, accessToken!);
      setComments(data);
    } catch (err: any) {
      setError(err.message || "Failed to load comments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadComments();
  }, [testCaseId]);

  const handleSubmit = async () => {
    if (!newComment.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      await addComment(
        testCaseId,
        {
          comment_text: newComment,
          parent_comment_id: replyingTo || undefined,
        },
        accessToken!
      );
      setNewComment("");
      setReplyingTo(null);
      await loadComments();
    } catch (err: any) {
      setError(err.message || "Failed to add comment");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <MessageCircle className="w-5 h-5" />
          Comments ({comments.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Add Comment Form */}
        <div className="mb-6">
          {replyingTo && (
            <div className="mb-2 p-2 bg-blue-50 border border-blue-200 rounded-md flex items-center justify-between">
              <p className="text-sm text-blue-700">
                Replying to comment
              </p>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setReplyingTo(null)}
                className="text-xs"
              >
                Cancel
              </Button>
            </div>
          )}
          <div className="flex gap-2">
            <Textarea
              placeholder="Add a comment..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              className="flex-1"
              rows={3}
            />
            <Button
              onClick={handleSubmit}
              disabled={submitting || !newComment.trim()}
              className="self-end"
            >
              <Send className="w-4 h-4 mr-1" />
              {submitting ? "Posting..." : "Post"}
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Comments List */}
        {loading ? (
          <div className="text-center py-8 text-gray-500">
            Loading comments...
          </div>
        ) : comments.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <MessageCircle className="w-12 h-12 mx-auto mb-2 text-gray-300" />
            <p>No comments yet. Be the first to comment!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {comments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                testCaseId={testCaseId}
                onReply={setReplyingTo}
                onResolve={loadComments}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
