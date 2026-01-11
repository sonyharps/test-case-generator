import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CheckCircle, XCircle } from "lucide-react";
import { updateTestCaseApproval } from "@/api/testCases";
import { useAuth } from "@/store/auth.store";

interface ApprovalControlsProps {
  testCaseId: number;
  currentStatus: "draft" | "approved" | "rejected";
  onApprovalChange: () => void;
}

export function ApprovalControls({
  testCaseId,
  currentStatus,
  onApprovalChange,
}: ApprovalControlsProps) {
  const accessToken = useAuth((state) => state.accessToken);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleApprove = async () => {
    setLoading(true);
    setError(null);

    try {
      await updateTestCaseApproval(
        testCaseId,
        { status: "approved" },
        accessToken!
      );
      onApprovalChange();
    } catch (err: any) {
      setError(err.message || "Failed to approve test case");
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!rejectionReason.trim()) {
      setError("Rejection reason is required");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await updateTestCaseApproval(
        testCaseId,
        { status: "rejected", rejection_reason: rejectionReason },
        accessToken!
      );
      setShowRejectModal(false);
      setRejectionReason("");
      onApprovalChange();
    } catch (err: any) {
      setError(err.message || "Failed to reject test case");
    } finally {
      setLoading(false);
    }
  };

  const handleRevertToDraft = async () => {
    setLoading(true);
    setError(null);

    try {
      await updateTestCaseApproval(
        testCaseId,
        { status: "draft" },
        accessToken!
      );
      onApprovalChange();
    } catch (err: any) {
      setError(err.message || "Failed to revert to draft");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {error && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="flex gap-2">
        {currentStatus === "draft" && (
          <>
            <Button
              size="sm"
              className="bg-green-600 hover:bg-green-700"
              onClick={handleApprove}
              disabled={loading}
            >
              <CheckCircle className="w-4 h-4 mr-1" />
              Approve
            </Button>
            <Button
              size="sm"
              variant="destructive"
              onClick={() => setShowRejectModal(true)}
              disabled={loading}
            >
              <XCircle className="w-4 h-4 mr-1" />
              Reject
            </Button>
          </>
        )}

        {(currentStatus === "approved" || currentStatus === "rejected") && (
          <Button
            size="sm"
            variant="outline"
            onClick={handleRevertToDraft}
            disabled={loading}
          >
            Revert to Draft
          </Button>
        )}
      </div>

      {/* Reject Modal */}
      <Dialog open={showRejectModal} onOpenChange={setShowRejectModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Test Case</DialogTitle>
            <DialogDescription>
              Please provide a reason for rejecting this test case. This will help improve
              future test case generation.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Textarea
              placeholder="Explain why this test case is being rejected..."
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="min-h-[120px]"
            />
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowRejectModal(false);
                setRejectionReason("");
                setError(null);
              }}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={loading || !rejectionReason.trim()}
            >
              {loading ? "Rejecting..." : "Reject Test Case"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
