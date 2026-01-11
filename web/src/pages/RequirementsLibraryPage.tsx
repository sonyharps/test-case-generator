// src/pages/RequirementsLibraryPage.tsx
import { useEffect, useState } from "react";
import { useAuth } from "@/store/auth.store";
import {
  getRequirements,
  createRequirement,
  updateRequirement,
  deleteRequirement,
  useRequirement,
  type Requirement,
  type RequirementCreate,
} from "@/api/requirements";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Plus, Edit, Trash2, BookMarked, Search } from "lucide-react";
import { useOrchestrator } from "@/store/orchestrator.store";
import { useNavigate } from "react-router-dom";

export default function RequirementsLibraryPage() {
  const accessToken = useAuth((state) => state.accessToken);
  const setRequirement = useOrchestrator((state) => state.setRequirement);
  const navigate = useNavigate();

  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingRequirement, setEditingRequirement] = useState<Requirement | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    tags: "",
    is_template: false,
  });

  useEffect(() => {
    if (accessToken) {
      loadRequirements();
    } else {
      setLoading(false);
    }
  }, [accessToken]);

  const loadRequirements = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getRequirements(accessToken!, 0, 100, searchTerm);
      setRequirements(response.requirements);
    } catch (err: any) {
      setError(err.message || "Failed to load requirements");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadRequirements();
  };

  const handleCreate = () => {
    setEditingRequirement(null);
    setFormData({ title: "", description: "", tags: "", is_template: false });
    setShowModal(true);
  };

  const handleEdit = (requirement: Requirement) => {
    setEditingRequirement(requirement);
    setFormData({
      title: requirement.title,
      description: requirement.description,
      tags: requirement.tags || "",
      is_template: requirement.is_template,
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    setError(null);
    try {
      if (editingRequirement) {
        // Update
        await updateRequirement(editingRequirement.id, formData, accessToken!);
      } else {
        // Create
        await createRequirement(formData as RequirementCreate, accessToken!);
      }
      setShowModal(false);
      loadRequirements();
    } catch (err: any) {
      setError(err.message || "Failed to save requirement");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this requirement?")) return;

    setError(null);
    try {
      await deleteRequirement(id, accessToken!);
      loadRequirements();
    } catch (err: any) {
      setError(err.message || "Failed to delete requirement");
    }
  };

  const handleUse = async (requirement: Requirement) => {
    try {
      await useRequirement(requirement.id, accessToken!);
      setRequirement(requirement.description);
      navigate("/orchestrator");
    } catch (err: any) {
      setError(err.message || "Failed to use requirement");
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Requirements Library</h2>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Requirements Library</h2>
          <p className="text-gray-600 mt-1">Save and reuse common requirements</p>
        </div>
        <Button onClick={handleCreate} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Requirement
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search requirements..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
                className="pl-10"
              />
            </div>
            <Button onClick={handleSearch} variant="outline">
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-4">
            <p className="text-red-700">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Requirements Grid */}
      {requirements.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center text-gray-500">
            <BookMarked className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium">No requirements yet</p>
            <p className="text-sm mt-2">Create your first requirement to get started</p>
            <Button onClick={handleCreate} className="mt-4">
              Create Requirement
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {requirements.map((req) => (
            <Card key={req.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 text-lg">{req.title}</h3>
                    {req.tags && (
                      <div className="flex gap-1 mt-2">
                        {req.tags.split(",").map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                          >
                            {tag.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  {req.is_template && (
                    <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                      Template
                    </span>
                  )}
                </div>

                <p className="text-gray-600 text-sm mb-4 line-clamp-3">{req.description}</p>

                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Used {req.usage_count} times</span>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="default"
                      onClick={() => handleUse(req)}
                      className="flex items-center gap-1"
                    >
                      Use
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleEdit(req)}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDelete(req.id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl">
            <CardContent className="p-6">
              <h3 className="text-xl font-bold mb-4">
                {editingRequirement ? "Edit Requirement" : "New Requirement"}
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Title *
                  </label>
                  <Input
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="e.g., User Login Flow"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description *
                  </label>
                  <Textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Describe the requirement in detail..."
                    rows={6}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tags (comma-separated)
                  </label>
                  <Input
                    value={formData.tags}
                    onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                    placeholder="e.g., authentication, security, login"
                  />
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_template"
                    checked={formData.is_template}
                    onChange={(e) => setFormData({ ...formData, is_template: e.target.checked })}
                    className="mr-2"
                  />
                  <label htmlFor="is_template" className="text-sm text-gray-700">
                    Mark as reusable template
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <Button variant="outline" onClick={() => setShowModal(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSave} disabled={!formData.title || !formData.description}>
                  {editingRequirement ? "Update" : "Create"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
