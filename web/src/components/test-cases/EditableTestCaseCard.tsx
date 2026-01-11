import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Edit, Save, X, History, CheckCircle, XCircle, Clock } from "lucide-react";
import { editTestCase, type TestCaseEditRequest } from "@/api/testCases";
import { useAuth } from "@/store/auth.store";

interface TestCase {
  id: number;
  tc_id: string;
  title: string;
  preconditions: string[];
  steps: string[];
  expected_result: string[];
  status?: "draft" | "approved" | "rejected";
  edit_count?: number;
  edited_by?: string | null;
  edited_at?: string | null;
}

interface EditableTestCaseCardProps {
  testCase: TestCase;
  onUpdate: () => void;
}

export function EditableTestCaseCard({ testCase, onUpdate }: EditableTestCaseCardProps) {
  const accessToken = useAuth((state) => state.accessToken);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Edit state
  const [editedTitle, setEditedTitle] = useState(testCase.title);
  const [editedPreconditions, setEditedPreconditions] = useState(
    testCase.preconditions.join("\n")
  );
  const [editedSteps, setEditedSteps] = useState(testCase.steps.join("\n"));
  const [editedExpectedResult, setEditedExpectedResult] = useState(
    testCase.expected_result.join("\n")
  );

  const handleEdit = () => {
    setIsEditing(true);
    setError(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedTitle(testCase.title);
    setEditedPreconditions(testCase.preconditions.join("\n"));
    setEditedSteps(testCase.steps.join("\n"));
    setEditedExpectedResult(testCase.expected_result.join("\n"));
    setError(null);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);

    try {
      const editData: TestCaseEditRequest = {
        title: editedTitle,
        preconditions: editedPreconditions.split("\n").filter((line) => line.trim()),
        steps: editedSteps.split("\n").filter((line) => line.trim()),
        expected_result: editedExpectedResult.split("\n").filter((line) => line.trim()),
      };

      await editTestCase(testCase.id, editData, accessToken!);
      setIsEditing(false);
      onUpdate(); // Refresh the test case data
    } catch (err: any) {
      setError(err.message || "Failed to save changes");
    } finally {
      setSaving(false);
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "approved":
        return (
          <Badge className="bg-green-100 text-green-800 border-green-200">
            <CheckCircle className="w-3 h-3 mr-1" />
            Approved
          </Badge>
        );
      case "rejected":
        return (
          <Badge className="bg-red-100 text-red-800 border-red-200">
            <XCircle className="w-3 h-3 mr-1" />
            Rejected
          </Badge>
        );
      default:
        return (
          <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">
            <Clock className="w-3 h-3 mr-1" />
            Draft
          </Badge>
        );
    }
  };

  return (
    <Card className="mb-4">
      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-gray-500">{testCase.tc_id}</span>
            {testCase.status && getStatusBadge(testCase.status)}
            {testCase.edit_count && testCase.edit_count > 0 && (
              <Badge variant="outline" className="text-xs">
                <History className="w-3 h-3 mr-1" />
                Edited {testCase.edit_count}x
              </Badge>
            )}
          </div>
          <div className="flex gap-2">
            {!isEditing ? (
              <Button size="sm" variant="outline" onClick={handleEdit}>
                <Edit className="w-4 h-4 mr-1" />
                Edit
              </Button>
            ) : (
              <>
                <Button size="sm" variant="outline" onClick={handleCancel} disabled={saving}>
                  <X className="w-4 h-4 mr-1" />
                  Cancel
                </Button>
                <Button size="sm" onClick={handleSave} disabled={saving}>
                  <Save className="w-4 h-4 mr-1" />
                  {saving ? "Saving..." : "Save"}
                </Button>
              </>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Title */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
          {isEditing ? (
            <Input
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              className="w-full"
            />
          ) : (
            <p className="text-gray-900 font-medium">{testCase.title}</p>
          )}
        </div>

        {/* Preconditions */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Preconditions
          </label>
          {isEditing ? (
            <Textarea
              value={editedPreconditions}
              onChange={(e) => setEditedPreconditions(e.target.value)}
              className="w-full min-h-[80px]"
              placeholder="One precondition per line"
            />
          ) : (
            <ul className="list-disc list-inside space-y-1">
              {testCase.preconditions.map((pre, idx) => (
                <li key={idx} className="text-sm text-gray-700">
                  {pre}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Steps */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Steps</label>
          {isEditing ? (
            <Textarea
              value={editedSteps}
              onChange={(e) => setEditedSteps(e.target.value)}
              className="w-full min-h-[120px]"
              placeholder="One step per line"
            />
          ) : (
            <ol className="list-decimal list-inside space-y-1">
              {testCase.steps.map((step, idx) => (
                <li key={idx} className="text-sm text-gray-700">
                  {step}
                </li>
              ))}
            </ol>
          )}
        </div>

        {/* Expected Result */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Expected Result
          </label>
          {isEditing ? (
            <Textarea
              value={editedExpectedResult}
              onChange={(e) => setEditedExpectedResult(e.target.value)}
              className="w-full min-h-[80px]"
              placeholder="One expected result per line"
            />
          ) : (
            <ul className="list-disc list-inside space-y-1">
              {testCase.expected_result.map((result, idx) => (
                <li key={idx} className="text-sm text-gray-700">
                  {result}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Edit History */}
        {testCase.edited_by && testCase.edited_at && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Last edited by {testCase.edited_by} on{" "}
              {new Date(testCase.edited_at).toLocaleString()}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
